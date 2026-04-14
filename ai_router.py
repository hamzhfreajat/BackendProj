import os
import json
import base64
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

import models
from database import get_db

try:
    from google import genai as _genai_new
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    _USE_NEW_SDK = False

router = APIRouter(prefix="/api/ai", tags=["ai"])

def _get_api_key():
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GOOGLE_API_KEY.")
    return api_key

@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Visual AI: Processes the first uploaded image to detect category and quality.
    """
    api_key = _get_api_key()
    
    try:
        content = await file.read()
        mime_type = file.content_type or "image/jpeg"
        if mime_type == "application/octet-stream":
            mime_type = "image/jpeg"
        # We need to pass the image to Gemini
        
        # Get list of category names to help Gemini choose
        categories = [c.name for c in db.query(models.Category).all()]
        cat_list_str = ", ".join(categories)

        prompt = f"""
        You are an expert AI for a classifieds app in Jordan.
        Analyze this image and return a JSON object with two keys:
        1. 'category_name': The best matching category for this item from this list: [{cat_list_str}]. If none matches well, suggest a broad term like 'سيارات' or 'عقارات'.
        2. 'image_quality': An assessment of the image quality. Must be strictly one of: 'good', 'blurry', 'dark'.

        Respond ONLY with the JSON object. Example:
        {{"category_name": "سيارات للبيع", "image_quality": "good"}}
        """

        if _USE_NEW_SDK:
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    prompt,
                    _genai_new.types.Part.from_bytes(data=content, mime_type=mime_type)
                ]
            )
            raw = response.text.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            image_part = {"mime_type": mime_type, "data": content}
            response = model.generate_content([prompt, image_part])
            raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        parsed = json.loads(raw.strip())
        return parsed

    except Exception as e:
        print(f"Error analyzing image: {e}")
        # Graceful fallback
        return {"category_name": None, "image_quality": "good"}

@router.post("/location-intelligence")
def location_intelligence(request: dict):
    """
    Returns landmarks near the given region and city in Jordan.
    Uses Gemini to synthesize nearby landmarks if lat/lng not strictly coded.
    """
    api_key = _get_api_key()
    region = request.get("region", "")
    city = request.get("city", "")
    
    if not region and not city:
        return {"landmarks": []}

    prompt = f"""
    You are a local Jordanian real estate and location expert. 
    The user is adding an ad in: City: {city}, Region: {region}.
    Provide 3 famous nearby landmarks or services (malls, universities, hospitals, major streets) and an estimated driving time in minutes.
    
    Return a JSON array of strings. Example:
    [
      "القرب من مكة مول - 3 دقائق",
      "بجانب مستشفى الحسين للسرطان",
      "قريب من شارع مكة"
    ]
    Respond ONLY with the JSON array.
    """
    try:
        if _USE_NEW_SDK:
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = response.text.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
                
        return {"landmarks": json.loads(raw.strip())}
    except Exception as e:
        print(f"Location Intelligence error: {e}")
        return {"landmarks": []}

@router.post("/price-estimate")
def price_estimate(request: dict, db: Session = Depends(get_db)):
    """
    Calculates the median/average price of similar ads.
    """
    cat_id = request.get("category_id")
    region = request.get("region")
    
    if not cat_id:
        return {"average_price": 0, "message": ""}
        
    query = db.query(func.avg(models.Ad.price)).filter(
        models.Ad.category_id == cat_id,
        models.Ad.price > 0
    )
    
    if region:
        query = query.filter(models.Ad.location.ilike(f"%{region}%"))
        
    avg = query.scalar()
    
    if not avg:
        # Fallback to category only
        avg = db.query(func.avg(models.Ad.price)).filter(
            models.Ad.category_id == cat_id,
            models.Ad.price > 0
        ).scalar()
        
    if avg and avg > 0:
        avg_int = int(avg)
        low_range = int(avg_int * 0.9)
        high_range = int(avg_int * 1.1)
        return {
            "average_price": avg_int,
            "message": f"بناءً على الإعلانات المشابهة في منطقتك، متوسط السعر في السوق هو {low_range} - {high_range} دينار."
        }
    
    return {"average_price": 0, "message": "لا توجد بيانات كافية لتقدير السعر المتوسط لهذا القسم حتى الآن."}

@router.post("/evaluate-ad")
def evaluate_ad(request: dict):
    """
    AI Coach: Evaluates the complete ad payload right before publishing.
    """
    api_key = _get_api_key()
    
    prompt = f"""
    You are an expert sales coach for a classifieds platform in Jordan.
    Evaluate the following ad details and provide:
    1. A 'score' out of 100 for how strong and convincing the ad is.
    2. A list of 2 or 3 short 'tips' (in Arabic) to improve it (e.g. "أضف المزيد من الصور", "وصفك ممتاز ومفصل!", "السعر قد يكون مرتفعاً قليلاً").
    
    Ad Data:
    {json.dumps(request, ensure_ascii=False)}
    
    Return a JSON object:
    {{"score": 85, "tips": ["نصيحة 1", "نصيحة 2"]}}
    Respond ONLY with JSON.
    """
    
    try:
        if _USE_NEW_SDK:
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = response.text.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
                
        return json.loads(raw.strip())
    except Exception as e:
        print(f"Evaluate Ad error: {e}")
        return {"score": 75, "tips": ["تأكد من إرفاق صور واضحة للحصول على مشاهدات أكثر"]}

@router.post("/generate-suggestions")
def generate_ad_suggestions(request: dict):
    """
    Generative AI: Title, Description, and Smart Tags.
    """
    api_key = _get_api_key()
    
    prompt = f"""
    أنت خبير محترف في تسويق الإعلانات المبوبة وصياغة نصوص إعلانية جذابة ومقنعة (Copywriter) للجمهور العربي (خاصة في الأردن). 

    بناءً على المعلومات التالية التي أدخلها المستخدم، قم بتأليف **3 خيارات مختلفة ومميزة** لعنوان الإعلان (Title) ووصف الإعلان (Description).
    قم أيضاً باستخراج **3 إلى 5 كلمات مفتاحية (Tags)** ذكية ومناسبة للإعلان ككل.
    
    المعلومات المدخلة من المستخدم:
    {json.dumps(request, ensure_ascii=False, indent=2)}

    قم بإرجاع النتيجة حصرياً بصيغة JSON، يحتوي على مصفوفة "suggestions" ومصفوفة "smart_tags".
    لا تقم بإضافة أي نصوص أخرى أو Markdowns خارج سياق الـ JSON. 

    المثال المطلوب:
    {{
      "suggestions": [
        {{ "title": "عنوان جذاب 1", "description": "وصف مقنع ومفصل 1" }},
        {{ "title": "عنوان جذاب 2", "description": "وصف مقنع ومفصل 2" }}
      ],
      "smart_tags": ["كلمة مفتاحية 1", "كلمة مفتاحية 2", "كلمة مفتاحية 3"]
    }}
    """
    
    try:
        if _USE_NEW_SDK:
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = response.text.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
                
        return json.loads(raw.strip())
    except Exception as e:
        print(f"Suggestions error: {e}")
        raise HTTPException(status_code=500, detail="فشل في توليد الاقتراحات")

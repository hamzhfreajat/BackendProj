"""
fb_batch_router.py - Facebook Posts Batch Ingestion Endpoint
============================================================
Add this router to main.py:

    from fb_batch_router import router as fb_batch_router
    app.include_router(fb_batch_router)
"""

import os
import json
import logging
import pathlib
import io
import uuid
import requests
import re
import concurrent.futures
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from extraction_constants import REAL_ESTATE_CATEGORIES
from mapper import get_location_map, get_category_map, map_location, map_category

from dotenv import load_dotenv
_this_dir = pathlib.Path(__file__).resolve().parent
load_dotenv(_this_dir / ".env", override=True)

# Fetch keys directly from environment variables. Do not hardcode them.
logger = logging.getLogger(__name__)

if not os.getenv("GOOGLE_API_KEY"):
    logger.warning("GOOGLE_API_KEY is missing from environment. AI processing might fail.")
# Project imports
from database import get_db
import models
from models import SourceType
import schemas
router = APIRouter(prefix="/api", tags=["fb-batch"])

print(f"[fb_batch_router] LOADED — will use source_type = {SourceType.SCRAPER_BOT}")


# -- Pydantic models --------------------------------------------------------

class FbPost(BaseModel):
    index: Optional[int] = None
    author: Optional[str] = None
    timestamp: Optional[str] = None
    postUrl: Optional[str] = None
    text: Optional[str] = None
    images: Optional[List[str]] = []
    reactions: Optional[str] = None
    scrapedAt: Optional[str] = None

class FbBatchRequest(BaseModel):
    posts: List[FbPost]
    category_id: Optional[int] = None
    default_location: Optional[str] = ""

class PostResult(BaseModel):
    index: int
    status: str          # "saved" | "skipped" | "error"
    ad_id: Optional[int] = None
    title: Optional[str] = None
    reason: Optional[str] = None

class FbBatchResponse(BaseModel):
    total: int
    saved: int
    skipped: int
    errors: int
    results: List[PostResult]


# -- Gemini: ONE call for ALL posts ------------------------------------------

_GEMINI_BATCH_PROMPT = """You are an AI assistant that extracts structured classified-ad data from Facebook posts.

Below is a numbered list of Facebook posts representing real classified ads (usually referencing locations in Jordan).
For EACH post, extract the following fields:
- index        (int) -- the post number as given
- title        (string, max 120 chars) -- a concise, clear ad title
- description  (string) -- rewrite and regenerate the description from scratch using the best SEO optimization language and highly engaging Arabic phrasing. Do NOT copy the original text directly. Make it sound like a premium, professional classified ad.
- price        (float) -- Extract the exact numeric price. Support eastern arabic numbers (e.g. ٥٠ دينار is 50.0). Look carefully for implicit rent/sale numbers. Return 0.0 ONLY if strictly missing. Do not return strings!
- location     (string) -- The geographic location. For real estate/apartments, format as 'المدينة, المنطقة' (e.g. عمان, عبدون). For lands (الأراضي), format as 'المحافظة, المديرية, القرية, الحوض' if mentioned (e.g. إربد, لواء بني كنانة, عقربا, حوض البلد). Keep empty if not found.
- phone_number (string or null) -- phone number if mentioned
- category_id  (int) -- Map to the MOST SPECIFIC deepest sub-category ID from the list (never use generic ID 3 if a deeper one like 301 or 3061 fits perfectly!). CRITICAL RULE: Analyze the intent of the author. If the author is SEEKING, ASKING FOR, or REQUESTING an apartment or roommate (meaning they do NOT have a property to offer, but are looking for one), set category_id to 0 to explicitly reject the post. Only accept posts where the author is realistically OFFERING a property or room.
- suggested_tags (list of strings) -- Array of specific feature keywords mentioned in the ad (e.g. "غرفة مفروشة", "طابق ارضي", "اوتوماتيك")
- attributes (object) -- Extract these specific property/shared-room features if mentioned:
    - rooms (int) -- Number of rooms
    - bathrooms (int) -- Number of bathrooms
    - furnished (string) -- Match exactly: مفروشة, غير مفروشة, مفروش جزئياً
    - floor (string) -- Match exactly: طابق التسوية, طابق شبه أرضي, الطابق الأرضي, 1, 2, 3, 4, 5, 6, 7
    - key_features (list[string]) -- Match exactly if possible: تكييف مركزي, تدفئة, شرفة / بلكونة, غرفة خادمة, غرفة غسيل, خزائن حائط, مسبح خاص, سخان شمسي, زجاج شبابيك مزدوج
    - room_type (string) -- غرفة خاصة, غرفة مشتركة, سرير في غرفة, استوديو ملحق بالسكن
    - target_audience (list[string]) -- شباب, طلاب, بنات, عائلات
    - room_capacity (string) -- شخص واحد, شخصين
    - current_occupants (int) -- Number of people currently in apartment
    - rent_duration (string) -- Match exactly: يومي, أسبوعي, شهري, كل 3 أشهر, كل أربع أشهر, كل 5 أشهر, كل 6 أشهر, سنوي
    - rent_includes (list[string]) -- الكهرباء, الماء, الإنترنت, التدفئة
    - payment_frequency (string) -- دفع شهري, دفع كل 3 شهور
    - insurance_required (bool)
    - bathroom_type (string) -- حمام ماستر, حمام مشترك
    - room_contents (list[string]) -- سرير مفرد, خزانة, شاشة
    - room_features (list[string]) -- مكيف مستقل, رديتر, بلكونة
    - shared_spaces (list[string]) -- صالة جلوس واسعة, طاولة طعام
    - kitchen_appliances (list[string]) -- ثلاجة, مايكرويف, غسالة
    - laundry_appliances (list[string]) -- غسالة, نشافة
    - smoking_rules (string) -- التدخين مسموح, يمنع التدخين
    - quietness_rules (string) -- سكن هادئ جداً, سكن مرن
    - guests_rules (string) -- مسموح بالزوار, يمنع الزوار
    - pets_rules (string) -- مسموح, يمنع
    - cleaning_rules (string)
    - building_age (string) -- Match exactly: 0 - 11 شهر, 1 - 5 سنوات, 6 - 9 سنوات, 10 - 19 سنوات, +20 سنة
    - building_features (list[string]) -- Match exactly if possible: يوجد مصعد, حديقة, موقف سيارات, حارس / أمن وحماية, كراج تفك, منطقة شواء, نظام كهرباء احتياطي للطوارئ, بركة سباحة, انتركم
    - land_type (string) -- Match exactly: سكنية, تجارية, زراعية, صناعية, استثمارية, سياحية, مختلطة, أخرى
    - zoning_classification (string) -- Match exactly: سكن أ, سكن ب, سكن ج, سكن د, تجاري, زراعي, صناعي, أخرى
    - facade (string) -- Match exactly: شمالية, جنوبية, شرقية, غربية, شمالية شرقية, شمالية غربية, جنوبية شرقية, جنوبية غربية
    - geometric_shape (string) -- Match exactly: مستطيل, مربع, غير منتظم, زاوية / شارعَين
    - topography (string) -- Match exactly: مستوية, منحدرة, جبلية, واد
    - available_services (list[string]) -- Match exactly: ماء, كهرباء, صرف صحي, إنترنت, شوارع معبدة
    - ownership_type (string) -- Match exactly: ملك, تفويض, أخرى
    - is_mortgaged (string) -- Match exactly: نعم, لا
    - installment_possible (string) -- Match exactly: نعم, لا
    - nearby_places (list[string]) -- جامعة, سوبر ماركت, قريبة من الباص

Return a JSON ARRAY where each element corresponds to one post.
Respond ONLY with valid JSON. No explanation, no markdown fences, no extra text.

=== CATEGORIES LIST ===
{categories_block}
=======================

=== POSTS ===
{posts_block}
"""

_GEMMA_SINGLE_PROMPT = """You are an expert real estate data extractor. Perform JSON extraction from the provided Facebook post. 

EXTREMELY IMPORTANT RULE FOR ARABIC: 
If the post contains the word "مطلوب" (Wanted/Seeking) or the author is ASKING to buy or rent an apartment, it is NOT a real estate offering! You MUST set category_id to 0 and provide a rejection_reason.

EXAMPLES OF CORRECT BEHAVIOR:
Example 1 (WANTED POST):
Post: "مطلوب شقة للايجار في الجبيهة بسعر رخيص"
Output: {{"title": "", "price": 0.0, "location": "", "phone_number": null, "category_name": "", "rejection_reason": "Author is seeking an apartment, not offering one", "suggested_tags": [], "attributes": {{}}}}

Example 2 (OFFERING POST - APARTMENT FOR SALE):
Post: "شقة للبيع في طبربور 3 غرف نوم بسعر 40 الف دينار 0791234567"
Output: {{"title": "شقة للبيع في طبربور 3 غرف نوم", "price": 40000.0, "location": "عمان, طبربور", "phone_number": "0791234567", "category_name": "شقق للبيع", "rejection_reason": "", "suggested_tags": ["للبيع", "طبربور", "3 غرف"], "attributes": {{"rooms": 3}}}}

Example 3 (OFFERING POST - APARTMENT FOR RENT):
Post: "شقة فارغة للايجار في دير غبارمكونه من ٣ نوم صالةمطبخ٢ حمام0795634384"
Output: {{"title": "شقة فارغة للإيجار في دير غبار", "price": 0.0, "location": "عمان, دير غبار", "phone_number": "0795634384", "category_name": "شقق للإيجار", "rejection_reason": "", "suggested_tags": ["شقة فارغة", "دير غبار", "إيجار"], "attributes": {{"rooms": 3, "bathrooms": 2, "furnished": "فارغة"}}}}

Now, process the following post. Respond ONLY with a JSON object.

Extract:
- title: (string) generate a concise, professional arabic title (Empty if category_id is 0)
- price: (float) numeric price (0.0 if missing)
- location: (string) Extract the exact city and region found in the post. Format as "City, Region" (e.g. "عمان, عبدون") if known, otherwise just output the region name.
- phone_number: (string or null) Look closely for 10-digit numbers.
- category_name: (string) Extract the exact real estate category (e.g. 'شقق للبيع', 'أراضي للإيجار', 'ستوديوهات'). Use empty string if author is SEEKING or if not offering real estate.
- rejection_reason: (string) If not offering real estate, provide exact reason why here.
- suggested_tags: (list[string]) 2-4 important keywords mentioned.
- attributes: (object) Extract basic properties into this object. Also CRITICALLY, create a nested "dynamic_data" object containing these EXACT keys if mentioned:
  - "dynamic_data": {{ 
      "area": (int), "bedrooms": (string), "bathrooms": (string), "furnishing": (string), "rent_duration": (string), "floor": (string), "age": (string), "main_features": (list[string]), "extra_features": (list[string]), "nearby": (list[string]), "facade": (string), "target_tenants": (list[string]), "property_restrictions": (list[string]), "building_fees_status": (list[string]), "water_supply": (list[string]), "cooling_features": (list[string]), "heating_features": (list[string]), "security_deposit_type": (string)
  }}

POST:
{post_text}

---
CRITICAL INSTRUCTION: Output ONLY valid JSON matching the exact schema requested. Do NOT output conversational text, explanations, or markdown like ```json. Start your response with {{ and end with }}.
"""


def _build_posts_block(posts: List[FbPost]) -> str:
    lines = []
    for i, p in enumerate(posts):
        idx = p.index or (i + 1)
        lines.append(f"--- Post #{idx} ---")
        lines.append(f"Text: {(p.text or '')[:300]}")
        lines.append("")
    return "\n".join(lines)

import threading
import time
import json
import os
from datetime import datetime

_GEMINI_LOCK = threading.Lock()
_LAST_GEMINI_CALL = 0.0

def _check_and_update_gemini_daily_limit() -> bool:
    """Returns True if under limits, False if 999 daily limit reached."""
    usage_file = "gemini_usage.json"
    today_str = datetime.now().strftime("%Y-%m-%d")
    try:
        if os.path.exists(usage_file):
            with open(usage_file, "r") as f:
                usage = json.load(f)
        else:
            usage = {"date": today_str, "count": 0}
            
        if usage.get("date") != today_str:
            usage = {"date": today_str, "count": 0}
            
        if usage["count"] >= 999:
            return False
            
        usage["count"] += 1
        with open(usage_file, "w") as f:
            json.dump(usage, f)
        return True
    except Exception:
        return True # Fail open safely if disk write fails


def _ai_process_chunk(chunk_posts: List[FbPost], categories_block: str) -> List[dict]:
    """Send a chunk of posts to an AI model with fallback logic."""
    api_key_gemini = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    api_key_deepseek = os.getenv("DEEPSEEK_API_KEY")
    api_key_grok = os.getenv("GROK_API_KEY")

    if not (api_key_gemini or api_key_deepseek or api_key_grok):
        raise RuntimeError("No API key set for any AI provider.")

    prompt = _GEMINI_BATCH_PROMPT.format(
        categories_block=categories_block,
        posts_block=_build_posts_block(chunk_posts)
    )

    errors = []

    def _parse_json_result(raw: str) -> List[dict]:
        logger.info("Parsing JSON...")
        try:
            # Strip markdown fences if present
            raw = raw.strip()
            # Regex to find the first JSON array or object
            match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
            if match:
                raw = match.group(1)
            
            # Clean up unescaped control characters (like raw tabs or newlines) which breaks standard json.loads
            raw = re.sub(r'[\x00-\x19]', ' ', raw)
            
            parsed = json.loads(raw)
            
            # Unpack if json_object wrapper is used (common for Deepseek/Grok JSON mode)
            if isinstance(parsed, dict) and len(parsed) == 1 and "posts" in parsed:
                parsed = parsed["posts"]
            elif isinstance(parsed, dict):
                parsed = [parsed]
                
            # Expand shortened keys to original format so _save_ad_to_db doesn't break
            expanded_parsed = []
            if isinstance(parsed, list):
                for item in parsed:
                    if not isinstance(item, dict): continue

                    cat_id = item.get("category_id")
                    rej_reason = ""
                    if cat_id == 0:
                        rej_reason = "Seeking property, explicitly rejected by AI rule"

                    raw_attrs = item.get("attributes", {})
                    if not isinstance(raw_attrs, dict): raw_attrs = {}

                    expanded_parsed.append({
                        "index": item.get("index") or item.get("i"),
                        "price": item.get("price") or item.get("p", 0.0),
                        "title": item.get("title") or item.get("tt", ""),
                        "description": item.get("description", ""),
                        "location": item.get("location") or item.get("l", ""),
                        "phone_number": item.get("phone_number") or item.get("ph"),
                        "category_id": cat_id,
                        "suggested_tags": item.get("suggested_tags") or item.get("t", []),
                        "rejection_reason": rej_reason,
                        "attributes": {
                            "dynamic_data": raw_attrs
                        }
                    })
                parsed = expanded_parsed
                
            logger.info("JSON successfully parsed.")
            return parsed
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing failed: {e}. Raw received: {raw[:200]}...")
            return []

    # 1. Try Local Gemma if enabled
    use_local_gemma = os.getenv("USE_LOCAL_GEMMA", "false").lower() == "true"
    if use_local_gemma:
        from openai import OpenAI
        
        gemma_base_url = os.getenv("GEMMA_BASE_URL", "http://localhost:11434/v1")
        gemma_api_key = os.getenv("GEMMA_API_KEY", "ollama") # Default for ollama
        gemma_model_name = os.getenv("GEMMA_MODEL_NAME", "gemma-classifieds")
        
        client = OpenAI(base_url=gemma_base_url, api_key=gemma_api_key)
        
        all_parsed = []
        for post in chunk_posts:
            single_prompt = _GEMMA_SINGLE_PROMPT.format(
                post_text=post.text
            )
            
            post_parsed = {"ai_chunk_error": "Gemma failed"}
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    logger.info(f"Trying Local Gemma (Attempt {attempt+1}/{max_retries})...")
                    response = client.chat.completions.create(
                        model=gemma_model_name,
                        messages=[{"role": "user", "content": single_prompt}],
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    
                    raw = response.choices[0].message.content
                    parsed_list = _parse_json_result(raw.strip())
                    if parsed_list and len(parsed_list) > 0:
                        post_parsed = parsed_list[0]
                        post_parsed["ai_model"] = gemma_model_name
                        post_parsed["raw_unparsed_chunk_layer"] = raw.strip()
                        break # success, exit retry loop
                        
                except Exception as e:
                    logger.warning(f"Local Gemma failed for post (Attempt {attempt+1}/{max_retries}): {e}")
                    post_parsed["ai_chunk_error"] = str(e)
                    time.sleep(1)
                    
            all_parsed.append(post_parsed)
            
        return all_parsed

    # 2. Try DeepSeek (if DEEPSEEK_API_KEY is provided), else try Gemini
    api_key_deepseek = os.getenv("DEEPSEEK_API_KEY")
    if not api_key_gemini and not api_key_deepseek:
        raise RuntimeError("No AI API keys provided (Gemini or DeepSeek).")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            if api_key_deepseek:
                logger.info(f"Trying DeepSeek AI (Attempt {attempt+1}/{max_retries})...")
                url = "https://api.deepseek.com/chat/completions"
                headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key_deepseek}"}
                payload = {
                    "model": "deepseek-chat",
                    "messages": [{"role": "system", "content": prompt}]
                }
                res = requests.post(url, json=payload, headers=headers, timeout=90)
                res.raise_for_status()
                data = res.json()
                raw = data["choices"][0]["message"]["content"]
                ai_model_used = "deepseek-chat"
            else:
                global _LAST_GEMINI_CALL
                sleep_time = 0.0
                with _GEMINI_LOCK:
                    if not _check_and_update_gemini_daily_limit():
                        logger.warning("Gemini Daily Limit (999) Reached! Failing.")
                        raise RuntimeError("Gemini Daily Limit Reached")

                    # Ensure 5.0 sec gap between requests (max 12 RPM)
                    now = time.time()
                    elapsed = now - _LAST_GEMINI_CALL
                    if elapsed < 5.0:
                        sleep_time = 5.0 - elapsed
                        _LAST_GEMINI_CALL = now + sleep_time
                    else:
                        _LAST_GEMINI_CALL = now

                if sleep_time > 0:
                    logger.info(f"Rate limiting Gemini: Sleeping {sleep_time:.2f}s outside lock to respect RPM limit")
                    time.sleep(sleep_time)

                logger.info(f"Trying Gemini AI (Attempt {attempt+1}/{max_retries})...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key_gemini}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "maxOutputTokens": 8192
                    }
                }
                
                res = requests.post(url, json=payload, headers=headers, timeout=60)
                res.raise_for_status()
                data = res.json()
                raw = data["candidates"][0]["content"]["parts"][0]["text"]
                ai_model_used = "gemini-2.5-flash-lite"

            parsed = _parse_json_result(raw.strip())
            for item in parsed:
                if isinstance(item, dict): 
                    item["ai_model"] = ai_model_used
                    item["raw_unparsed_chunk_layer"] = raw.strip()
            return parsed

        except Exception as e:
            # If the exception is Daily Limit, break out immediately
            if "Gemini Daily Limit Reached" in str(e):
                errors.append(str(e))
                break

            wait_sec = (attempt + 1) * 5
            logger.warning(f"Gemini failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_sec}s...")
            time.sleep(wait_sec)
            
    errors.append("Gemini failed after maximum retries.")

    logger.error("AI processing failed entirely.")
    raise RuntimeError(f"AI processing failed: {errors}")


def _ai_process_all(posts: List[FbPost], db: Session) -> List[dict]:
    """Process all posts in chunks to avoid token limits, running concurrently."""
    from extraction_constants import REAL_ESTATE_CATEGORIES
    # Supply exactly the categories list the user's prompt needs (includes mapping IDs)
    categories_block = REAL_ESTATE_CATEGORIES
    
    # Send ALL non-duplicate posts to AI safely in chunks
    # Keep chunk size explicitly to 20 to heavily reduce request count and overhead tokens.
    CHUNK_SIZE = 20
    chunks = [posts[i:i + CHUNK_SIZE] for i in range(0, len(posts), CHUNK_SIZE)]
    
    def process_single_chunk(chunk):
        try:
            logger.info(f"Sending chunk of {len(chunk)} posts to AI...")
            res = _ai_process_chunk(chunk, categories_block)
            if len(res) < len(chunk):
                # If AI returned fewer results, pad with an explicit error to avoid silent blanks
                res.extend([{"ai_chunk_error": "AI returned fewer items than requested (possible truncation)"}] * (len(chunk) - len(res)))
            return res[:len(chunk)]
        except Exception as e:
            logger.error(f"AI chunk failed: {e}. Falling back to default data for chunk.")
            return [{"ai_chunk_error": str(e)}] * len(chunk)

    all_results = []
    # Run all AI chunk processing concurrently (max 3 workers to prevent overwhelming free tier lock)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results_from_threads = executor.map(process_single_chunk, chunks)
        for chunk_res in results_from_threads:
            all_results.extend(chunk_res)

    return all_results


# -- DB helpers --------------------------------------------------------------

def _upload_imgs_to_r2(image_urls: List[str]) -> List[str]:
    if not image_urls:
        return []
    
    from media_router import get_r2_client
    r2_client = get_r2_client()
    if not r2_client:
        return image_urls
    
    bucket_name = os.getenv("R2_BUCKET_NAME", "joapp-ads")
    public_url = os.getenv("R2_PUBLIC_URL", "https://pub-158212dafa5344d4bbf078a74da2305a.r2.dev")
    public_url_base = public_url.rstrip('/')
    
    def process_url(url):
        if not url: return None
        if "r2.dev" in url or "cloudflare" in url:
            return url
            
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
                file_ext = ".png" if "png" in content_type else ".jpg"
                unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                file_obj = io.BytesIO(resp.content)
                
                r2_client.upload_fileobj(
                    file_obj, 
                    bucket_name, 
                    unique_filename,
                    ExtraArgs={'ContentType': content_type}
                )
                return f"{public_url_base}/{unique_filename}"
            else:
                return url
        except Exception as e:
            logger.error(f"Failed to upload FB image to R2 {url}: {e}")
            return url

    # Use ThreadPoolExecutor to upload all images concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_url, image_urls))
        
    return [r for r in results if r is not None]

def _get_or_create_ai_user(db: Session) -> models.User:
    ai_user = db.query(models.User).filter(models.User.username == "ai_scraper").first()
    if not ai_user:
        ai_user = models.User(
            username="ai_scraper",
            email="ai_scraper@system.local",
        )
        if hasattr(models.User, "hashed_password"):
            ai_user.hashed_password = "SYSTEM_NO_LOGIN"
        db.add(ai_user)
        db.commit()
        db.refresh(ai_user)
    return ai_user


def _is_duplicate(db: Session, source_url: str, raw_description: str) -> Optional[int]:
    if source_url:
        import re
        # 1. Check exact match
        ad = db.query(models.Ad).filter(models.Ad.source_url == source_url).first()
        if ad: return ad.id
            
        # 2. Extract FB Post ID and use LIKE matcher (handles tracking parameter changes)
        match = re.search(r'/posts/(\d+)', source_url)
        if match:
            post_id = match.group(1)
            ad = db.query(models.Ad).filter(models.Ad.source_url.like(f"%/posts/{post_id}%")).first()
            if ad: return ad.id
                
        match2 = re.search(r'story_fbid=(\d+)', source_url)
        if match2:
            post_id = match2.group(1)
            ad = db.query(models.Ad).filter(models.Ad.source_url.like(f"%story_fbid={post_id}%")).first()
            if ad: return ad.id

    return None
            
    return None
def _save_ad_to_db(db, post, ai_data, ai_user_id, fb_request_category_id, default_location):
    # Dynamically extract Category from AI category_name strings
    categories_map = get_category_map()
    ai_cat_name = ai_data.get("category_name", "")
    mapped_cat_id = 0
    if ai_cat_name:
        mapped_cat_id = map_category(ai_cat_name, categories_map)
        
    final_category_id = mapped_cat_id or ai_data.get("category_id") or fb_request_category_id or 3
    if ai_data.get("rejection_reason"):
        final_category_id = 0 # Enforce rejected 
    
    # Map explicit Region Locs
    location_map = get_location_map()
    ai_loc_str = ai_data.get("location", "")
    mapped_location = map_location(ai_loc_str, location_map) or default_location or ""

    # Generate smarter fallback title if AI extraction failed
    ad_title = ai_data.get("title")
    if not ad_title:
        if post.text:
            words = post.text.strip().split()
            ad_title = " ".join(words[:8]) + ("..." if len(words) > 8 else "")
        else:
            ad_title = f"إعلان من {post.author or 'مستخدم'}"

    # Handle AI nested attribute extraction safely
    ai_attrs = ai_data.get("attributes", {})
    if isinstance(ai_attrs, str):
        try:
            ai_attrs = json.loads(ai_attrs)
        except:
            ai_attrs = {}
    elif not isinstance(ai_attrs, dict):
        ai_attrs = {}

    # Handle AI price extraction safely
    raw_price = ai_data.get("price", 0.0)
    try:
        final_price = float(raw_price)
    except (ValueError, TypeError):
        final_price = 0.0

    from datetime import datetime, timedelta
    ad_created_at = None
    if post.timestamp:
        try:
            # Handle standard ISO formats from the JS scraper
            dt_str = post.timestamp.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            
            # The database stores naive standard time in Jordan Local Time (UTC+3)
            # Since the scraper sends UTC (Z) or offset-aware dates, we shift to +3 first
            dt = dt + timedelta(hours=3)
            
            ad_created_at = dt.replace(tzinfo=None) # Use naive datetime for SQLAlchemy TIMESTAMP
        except ValueError:
            pass

    ad = models.Ad(
        user_id=ai_user_id,
        title=ad_title,
        description=ai_data.get("description") or post.text or "",
        price=final_price,
        location=mapped_location,
        image_url=json.dumps(post.images) if post.images and len(post.images) > 0 else None,
        category_id=final_category_id,
        source_type=SourceType.SCRAPER_BOT,
        source_url=post.postUrl or None,
        raw_description=(post.text or "")[:8000] if post.text else None,
        attributes={
            **ai_attrs, # Spread AI extracted attributes safely
            "dynamic_data": ai_attrs.get("dynamic_data", {}), # Ensure it explicitly exists
            "author": post.author,
            "timestamp": post.timestamp,
            "reactions": post.reactions,
            "scraped_at": post.scrapedAt,
            "phone_number": ai_data.get("phone_number"),
            "images": post.images or [],
        },
        is_published=True,
    )
    
    if ad_created_at:
        ad.created_at = ad_created_at
    
    # Map AI extracted Tags
    suggested_tags = ai_data.get("suggested_tags", [])
    if isinstance(suggested_tags, list) and len(suggested_tags) > 0:
        dest_category = None
        if final_category_id:
            dest_category = db.query(models.Category).filter(models.Category.id == final_category_id).first()
            
        for tag_name in suggested_tags:
            if not isinstance(tag_name, str):
                continue
            clean_tag = tag_name.strip()
            if not clean_tag:
                continue
            tag = db.query(models.Tag).filter(models.Tag.name == clean_tag).first()
            if not tag:
                tag = models.Tag(name=clean_tag)
                db.add(tag)
            ad.linked_tags.append(tag)
            
            # Propagate the tag to the global category so Flutter renders it as a filter chip!
            if dest_category and tag not in dest_category.linked_tags:
                dest_category.linked_tags.append(tag)
            
    db.add(ad)
    db.commit()
    db.refresh(ad)
    
    # Extract dynamic properties for normalized Real Estate Details table
    dyn = ai_attrs.get("dynamic_data", {})
    if not isinstance(dyn, dict): dyn = {}
    
    # Safely extract area as integer
    raw_area = dyn.get("area") or ai_attrs.get("area")
    build_area_val = None
    if raw_area is not None:
        area_str = str(raw_area)
        # Extract just the digits
        digits = ''.join([c for c in area_str if c.isdigit()])
        if digits:
            build_area_val = int(digits)

    # Safely concatenate feature arrays ensuring no NoneType errors
    mf_dyn = dyn.get("main_features") or []
    if not isinstance(mf_dyn, list): mf_dyn = []
    kf_ai = ai_attrs.get("key_features") or []
    if not isinstance(kf_ai, list): kf_ai = []
    
    ef_dyn = dyn.get("extra_features") or []
    if not isinstance(ef_dyn, list): ef_dyn = []
    tt_dyn = dyn.get("target_tenants") or []
    if not isinstance(tt_dyn, list): tt_dyn = []
    pr_dyn = dyn.get("property_restrictions") or []
    if not isinstance(pr_dyn, list): pr_dyn = []
    
    nb_dyn = dyn.get("nearby") or []
    if not isinstance(nb_dyn, list): nb_dyn = []

    try:
        re_detail = models.AdRealEstateDetail(
            ad_id=ad.id,
            bathrooms=int(dyn.get("bathrooms", 0)) if str(dyn.get("bathrooms", "")).isdigit() else ai_attrs.get("bathrooms"),
            furnished=str(dyn.get("furnishing")) if dyn.get("furnishing") else str(ai_attrs.get("furnished", "")),
            build_area=build_area_val,
            floor=str(dyn.get("floor")) if dyn.get("floor") else str(ai_attrs.get("floor", "")),
            rent_duration=str(dyn.get("rent_duration")) if dyn.get("rent_duration") else str(ai_attrs.get("rent_duration", "")),
            view_orientation=str(dyn.get("facade")) if dyn.get("facade") else None,
            building_age=str(dyn.get("age")) if dyn.get("age") else None,
            key_features=mf_dyn + kf_ai,
            additional_features=ef_dyn + tt_dyn + pr_dyn,
            nearby_locations=nb_dyn
        )
        db.add(re_detail)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create Real Estate Details for bot ad: {e}")
    
    # TRIGGER NOTIFICATION ENGINE 
    from observer import trigger_saved_filter_notifications
    try:
        trigger_saved_filter_notifications(db, ad)
    except Exception as e:
        logger.error(f"Failed to trigger notifications: {e}")
        
    return ad


# -- Main endpoint -----------------------------------------------------------

@router.post("/fb-posts/batch", response_model=FbBatchResponse)
def ingest_fb_posts_batch(
    req: FbBatchRequest,
    db: Session = Depends(get_db),
):
    """
    Accept a batch of scraped Facebook posts, process ALL through
    Gemini AI in ONE request, then save each result to the database.
    """
    try:
        return _do_ingest(req, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unhandled error in batch endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _log_training_data(db: Session, post_text: str, ai_output: dict, status: str, reason: str, raw_response: str = None, ai_model: str = None):
    try:
        log_entry = models.AITrainingLog(
            post_text=post_text,
            status=status,
            ai_model=ai_model,
            ai_output=ai_output,
            reason=reason,
            raw_response=raw_response
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Training logger failed: {e}")

def _do_ingest(req: FbBatchRequest, db: Session):
    if not req.posts:
        raise HTTPException(status_code=400, detail="No posts provided.")

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("GROK_API_KEY")):
        raise HTTPException(status_code=500, detail="Missing AI API keys.")

    ai_user = _get_or_create_ai_user(db)
    results: List[PostResult] = []
    saved = skipped = errors = 0

    # Step 1: Filter duplicates and empty posts BEFORE calling AI
    posts_to_process: List[FbPost] = []
    post_index_map: dict = {}
    # Separate sets for URL and Text intra-batch deduplication
    seen_in_batch_urls = set()
    seen_in_batch_texts = set()

    for i, post in enumerate(req.posts):
        idx = post.index or (i + 1)

        if not post.text and not post.postUrl:
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="No text or URL"))
            continue

        dup_ad_id = _is_duplicate(db, post.postUrl or "", post.text or "")
        if dup_ad_id:
            skipped += 1
            reason = f"Duplicate post (Matches Ad ID {dup_ad_id})"
            _log_training_data(db, post.text or "", {"dup_ad_id": dup_ad_id}, "skipped", reason)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue
            
        # Intra-batch duplicate check (prevents sending identical posts to AI if they were both scraped just now)
        unique_key_url = None
        if post.postUrl:
            match = re.search(r'/posts/(\d+)', post.postUrl)
            if match:
                unique_key_url = f"post_{match.group(1)}"
            else:
                match2 = re.search(r'story_fbid=(\d+)', post.postUrl)
                if match2:
                    unique_key_url = f"story_{match2.group(1)}"
        
        unique_key_text = None
        is_intra_dup = False
        if unique_key_url and unique_key_url in seen_in_batch_urls:
            is_intra_dup = True
            
        if is_intra_dup:
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="Duplicate post (in batch)"))
            continue
            
        if unique_key_url: seen_in_batch_urls.add(unique_key_url)

        raw_text = post.text or ""
        clean_text = re.sub(r'[\s-]', '', raw_text)
        if not re.search(r'\d{9,}', clean_text):
            skipped += 1
            results.append(PostResult(index=idx, status="skipped", reason="No phone number found"))
            continue

        post_index_map[len(posts_to_process)] = idx
        posts_to_process.append(post)

    if not posts_to_process:
        return FbBatchResponse(
            total=len(req.posts), saved=0, skipped=skipped, errors=0, results=results,
        )

    # Step 2: Send ALL non-duplicate posts to AI safely in chunks
    try:
        logger.info(f"Sending {len(posts_to_process)} posts to AI...")
        ai_results = _ai_process_all(posts_to_process, db)
        logger.info(f"AI returned {len(ai_results)} results")
    except Exception as e:
        logger.error(f"AI failed: {e}. Falling back to default data.")
        ai_results = [{"ai_chunk_error": f"SYSTEM_ERROR: {str(e)}"}] * len(posts_to_process)

    # Step 3: Save each AI result to the database
    for j, post in enumerate(posts_to_process):
        idx = post_index_map[j]
        ai_data = ai_results[j] if j < len(ai_results) else {}

        raw_res = None
        used_ai_model = None
        if isinstance(ai_data, dict):
            if "raw_unparsed_chunk_layer" in ai_data:
                raw_res = ai_data.pop("raw_unparsed_chunk_layer")
            if "ai_model" in ai_data:
                used_ai_model = ai_data.pop("ai_model")

        # 1. Output explicit AI Exceptions
        if isinstance(ai_data, dict) and "ai_chunk_error" in ai_data:
            skipped += 1
            reason = f"AI Error: {ai_data['ai_chunk_error']}"
            logger.error(f"Post #{idx} skipped: {reason}")
            _log_training_data(db, post.text or "", ai_data, "failed", reason, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue

        # 2. Skip if AI determined this is a "Looking for" post or rejected it explicitly
        if isinstance(ai_data, dict) and (ai_data.get("category_id") == 0 or not ai_data.get("category_name")):
            skipped += 1
            reason = ai_data.get("rejection_reason", "AI determined post is not offering real estate")
            logger.info(f"Post #{idx} rejected: {reason}")
            _log_training_data(db, post.text or "", ai_data, "rejected", reason, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="skipped", reason=reason))
            continue

        try:
            post.images = _upload_imgs_to_r2(post.images)
            ad = _save_ad_to_db(
                db=db, post=post, ai_data=ai_data,
                ai_user_id=ai_user.id,
                fb_request_category_id=req.category_id,
                default_location=req.default_location or "",
            )
            saved += 1
            _log_training_data(db, post.text or "", ai_data, "success", None, raw_res, used_ai_model)
            results.append(PostResult(index=idx, status="saved", ad_id=ad.id, title=ad.title))
            logger.info(f"Post #{idx} -> Ad ID {ad.id}: {ad.title}")
        except Exception as e:
            errors += 1
            logger.error(f"DB save failed for post #{idx}: {e}")
            results.append(PostResult(index=idx, status="error", reason=str(e)))

    return FbBatchResponse(
        total=len(req.posts), saved=saved, skipped=skipped, errors=errors, results=results,
    )

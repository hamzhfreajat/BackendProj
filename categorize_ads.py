import os
import time
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import google.generativeai as genai

from database import SessionLocal
import models

# Explicitly load .env from the same directory as script
import sys
sys.stdout.reconfigure(encoding='utf-8')

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
gemini_api_key = None
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'API_KEY=' in line:
                gemini_api_key = line.split('=', 1)[1].strip()
                break

# --- Pydantic Schema for Gemini Strict JSON Extraction ---
class ExtractedAdAttributes(BaseModel):
    rooms: Optional[int] = Field(description="Number of rooms, if mentioned")
    bathrooms: Optional[int] = Field(description="Number of bathrooms")
    furnished: Optional[str] = Field(description="Furnished state. Match with: مفروش كامل, فرش فندقي, شبه مفروش, غير مفروش")
    floor: Optional[str] = Field(description="Floor level. Match with: تسوية, شبه أرضي, أرضي, 1, 2, 3, 4, 5, 6, رووف")
    key_features: List[str] = Field(description="Array of general features like: تدفئة, تكييف إنفيرتر, مصعد, كراج, الخ")
    
    # 1. Basic Info (Shared Rooms)
    room_type: Optional[str] = Field(description="Type of room. Match with: غرفة خاصة, غرفة مشتركة, سرير في غرفة, استوديو ملحق بالسكن")
    target_audience: List[str] = Field(description="Who is this for? e.g. شباب, طلاب, بنات, عائلات صغيرة, وافدين")
    room_capacity: Optional[str] = Field(description="Room capacity if mentioned: شخص واحد, شخصين, 3 أشخاص, الخ")
    current_occupants: Optional[int] = Field(description="Total number of people currently in the apartment (e.g. 1, 2, 3...)")
    rent_duration: Optional[str] = Field(description="Duration: يومي, أسبوعي, شهري, فصل دراسي, سنوي")
    
    # 2. Cost & Bills
    rent_includes: List[str] = Field(description="What's included in rent: الكهرباء, الماء, الإنترنت, التدفئة, الغاز, حارس العمارة, غير شامل")
    payment_frequency: Optional[str] = Field(description="e.g. دفع شهري, دفع كل 3 شهور, دفع فصلي")
    insurance_required: Optional[bool] = Field(description="True if insurance/deposit is required, False if without insurance")
    
    # 3. Room Specs
    bathroom_type: Optional[str] = Field(description="Bathroom type: حمام ماستر, حمام مشترك مع شخص واحد, حمام مشترك مع باقي الشقة")
    room_contents: List[str] = Field(description="Items in room: سرير مفرد, سرير مزدوج, خزانة ملابس, مكتب دراسة, شاشة تلفزيون, ثلاجة صغيرة")
    room_features: List[str] = Field(description="Room perks: مكيف مستقل, رديتر تدفئة, مروحة سقف, بلكونة, شباك كبير")
    
    # 4. Shared Space Specs (Apartment)
    shared_spaces: List[str] = Field(description="Shared areas: صالة جلوس واسعة, طاولة طعام, تراس, حمام ضيوف")
    kitchen_appliances: List[str] = Field(description="Kitchen: مطبخ راكب, ثلاجة كبيرة, فريزر منفصل, غاز, مايكرويف, كولر ماء, جلاية")
    laundry_appliances: List[str] = Field(description="Laundry: غسالة أوتوماتيك, نشافة ملابس, مكواة, منشر غسيل")
    
    # 5. House Rules
    smoking_rules: Optional[str] = Field(description="Smoking: التدخين مسموح, التدخين مسموح في البلكونة فقط, مسموح بالتدخين الإلكتروني فقط, يمنع التدخين نهائياً")
    quietness_rules: Optional[str] = Field(description="Quietness: سكن هادئ جداً, سكن مرن")
    guests_rules: Optional[str] = Field(description="Guests: مسموح بالزوار, يمنع الزوار")
    pets_rules: Optional[str] = Field(description="Pets: مسموح, يمنع اصطحاب الحيوانات")
    cleaning_rules: Optional[str] = Field(description="Cleaning: جدول تنظيف مشترك, وجود عاملة نظافة")
    
    # 6. Building Specs
    building_age: Optional[str] = Field(description="Age of building: جديد لم يسكن, أقل من 5 سنوات, مجدد بالكامل, بناء قديم")
    building_features: List[str] = Field(description="Building perks: مصعد, حارس, كاميرات مراقبة, دخول ذكي, موقف سيارات, خزان ماء إضافي, جيم, مسبح")
    
    # 7. Locations
    nearby_places: List[str] = Field(description="Nearby: محطة الباص السريع, جامعة, سوبر ماركت, صيدلية, مطاعم")
    
    payment_method: List[str] = Field(description="How payment works? e.g. من المالك, مكتب عقاري, تقسيط")
    phone_number: Optional[str] = Field(description="Any extracted Jordanian phone number")

class AdCategoryUpdate(BaseModel):
    ad_id: int = Field(description="The unique database ID of the ad")
    category_id: int = Field(description="The ID of the category that best matches this post. Use the most specific sub-category possible.")
    suggested_tags: List[str] = Field(description="Array of specific feature keywords or tags explicitly mentioned in the ad text (e.g. 'غرفة مفروشة', 'طابق ارضي')")
    attributes: Optional[ExtractedAdAttributes] = Field(description="Detailed extracted features specific to real estate and shared rooms.")

def run():
    db = SessionLocal()
    # gemini_api_key is set globally above
    global gemini_api_key
    if not gemini_api_key:
        print("ERROR: API_KEY is not set.")
        return

    genai.configure(api_key=gemini_api_key)

    # 1. Fetch all categories and format them for the prompt
    print("Fetching categories from database...")
    db_categories = db.query(models.Category).all()
    categories_context_lines = []
    for cat in db_categories:
        # Build a hierarchy string if possible, or just the name and ID
        parent_name = ""
        if cat.parent_id:
            parent = next((p for p in db_categories if p.id == cat.parent_id), None)
            if parent:
                parent_name = f" (Child of {parent.name})"
        
        linked_tags_str = ", ".join([tag.name for tag in getattr(cat, 'linked_tags', [])]) if getattr(cat, 'linked_tags', []) else ""
        tags = f" | Tag: {cat.tag}" if cat.tag else ""
        keywords = f" | Keywords: {linked_tags_str}" if linked_tags_str else ""
        categories_context_lines.append(f"ID: {cat.id} | Name: {cat.name}{parent_name}{tags}{keywords}")
        
    categories_context = "\n".join(categories_context_lines)
    print(f"Loaded {len(db_categories)} categories.")

    # 2. Fetch ads that we want to categorize
    # Let's fetch all ads for now (you can add a filter here like models.Ad.category_id == None if needed)
    print("Fetching ads from database...")
    ads_to_process = db.query(models.Ad).all()
    print(f"Found {len(ads_to_process)} total ads.")

    system_instruction = (
        "You are an expert AI categorization assistant specialized in Jordanian classifieds ( العقارات, السيارات, الوظائف, etc ).\n"
        "You will receive an array of ads from the database.\n"
        "Your job is to read the ad text and map it to the PERFECT category ID from the provided list, and generate an array of descriptive 'suggested_tags'.\n"
        "Always try to use the MOST SPECIFIC sub-category (e.g. 'شقق للبيع' instead of just 'عقارات').\n\n"
        "Here are the available categories:\n"
        f"--- CATEGORIES LIST ---\n{categories_context}\n-----------------------\n\n"
        "For each ad, output its original `ad_id`, the best matching `category_id`, `suggested_tags` array, and carefully extract ALL possible fields into the `attributes` object."
    )

    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
    
    # Process in batches of 20 to avoid exceeding payload limits
    batch_size = 20
    processed_count = 0
    updated_count = 0

    for i in range(0, len(ads_to_process), batch_size):
        batch = ads_to_process[i:i+batch_size]
        prompts_array = []
        
        for ad in batch:
            text = ad.raw_description if ad.raw_description else ad.description
            prompts_array.append(f"Ad ID {ad.id}:\nTEXT: {text[:500]}") # limit text length per ad
            
        prompt_text = "Map the following ads to their correct category_id:\n\n" + "\n---\n".join(prompts_array)
        
        try:
            print(f"Sending batch {i//batch_size + 1} ({len(batch)} ads) to Gemini...")
            result = model.generate_content(
                prompt_text,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=list[AdCategoryUpdate],
                ),
            )
            
            import json
            raw_json = result.text.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json[7:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]
                    
            extracted_updates = json.loads(raw_json.strip())
            
            # Update DB
            for update in extracted_updates:
                ad_id = update.get("ad_id")
                new_cat_id = update.get("category_id")
                suggested_tags = update.get("suggested_tags", [])
                
                db_ad = next((a for a in batch if a.id == ad_id), None)
                if db_ad:
                    dirty = False
                    if new_cat_id and new_cat_id != 0 and db_ad.category_id != new_cat_id:
                        db_ad.category_id = new_cat_id
                        dirty = True
                        
                    # Merge new attributes into existing
                    new_attrs = update.get("attributes", {})
                    if new_attrs:
                        current_attrs = db_ad.attributes or {}
                        # Only update if there are new non-null values to avoid overwriting existing
                        merged_attrs = dict(current_attrs)
                        for k, v in new_attrs.items():
                            if v is not None and (not isinstance(v, list) or len(v) > 0):
                                merged_attrs[k] = v
                        db_ad.attributes = merged_attrs
                        dirty = True
                    
                    if isinstance(suggested_tags, list) and len(suggested_tags) > 0:
                        # Deduplicate internally to prevent UniqueViolation inside the same transaction
                        unique_tags = list(set(suggested_tags))
                        for tag_name in unique_tags:
                            if not isinstance(tag_name, str): continue
                            clean_tag = tag_name.strip()
                            if not clean_tag: continue
                                
                            tag = db.query(models.Tag).filter(models.Tag.name == clean_tag).first()
                            if not tag:
                                tag = models.Tag(name=clean_tag)
                                db.add(tag)
                                db.commit() # Commit instantly to avoid cross-ad race conditions
                                db.refresh(tag)
                            
                            if tag not in db_ad.linked_tags:
                                db_ad.linked_tags.append(tag)
                                dirty = True
                                
                    if dirty:
                        updated_count += 1
                        print(f"  [+] Ad {ad_id} mapped to Category {new_cat_id} with {len(suggested_tags)} tags")
            
            db.commit()
            processed_count += len(batch)
            print(f"Successfully processed {processed_count}/{len(ads_to_process)} ads.")
            time.sleep(2) # rate limit buffer
            
        except Exception as e:
            print(f"ERROR on batch {i//batch_size + 1}: {e}")
            db.rollback()
            time.sleep(5)
            
    db.close()
    print(f"\nDONE! Mapped and updated {updated_count} ads in the database.")

if __name__ == "__main__":
    run()

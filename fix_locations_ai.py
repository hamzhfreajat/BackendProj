import os
import json
import time
import sys
from database import SessionLocal
from models import Ad, City, Region
from sqlalchemy import or_

try:
    from google import genai as _genai_new
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    _USE_NEW_SDK = False

def log(msg):
    msg = str(msg)
    with open("fix_locations_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        # Fallback for Windows console if it can't print Arabic chars
        print(msg.encode('utf-8', errors='replace').decode('cp1252', errors='replace'), flush=True)

def get_all_regions():
    db = SessionLocal()
    try:
        regions = db.query(Region).join(City).all()
        return [f"{r.city.name_ar}, {r.name_ar}" for r in regions]
    finally:
        db.close()

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def process_ads_batch(ads_data, regions_list, api_key):
    prompt = f"""
    You are an expert Jordanian real estate and location assistant.
    I will provide you a list of ads that currently have "Others" or "أخرى" as their location.
    I will also provide you a list of ALL valid regions in Jordan in the format "City, Region".
    
    Your task is to read the title, description, and raw_description of each ad, and determine the exact valid region from the provided list.
    If you cannot determine the exact region from the text but you are HIGHLY CONFIDENT of the correct "City, Region" name (e.g. "عمان, تلاع العلي"), return that exact string even if it is not in the list. Do not use "أخرى" unless absolutely necessary.
    
    CRITICAL LOCATION RULES:
    1. In Aqaba (العقبة), "المنطقة الأولى" maps to "العقبة, السكنية 1", "المنطقة الثانية" maps to "العقبة, السكنية 2", "المنطقة الثالثة" maps to "العقبة, السكنية 3", "المنطقة الرابعة" maps to "العقبة, السكنية 4", "الخامسة" to "العقبة, السكنية 5", "السادسة" to "العقبة, السكنية 6", "السابعة" to "العقبة, السكنية 7", "الثامنة" to "العقبة, السكنية 8", "التاسعة" to "العقبة, السكنية 9", and "العاشرة" to "العقبة, السكنية 10".
    2. "الدوار الثالث", "الرابع", "الخامس", "السادس", "السابع", "الثامن" belong strictly to "عمان" (Amman). 
    3. "شفا بدران" is a distinct region in "عمان". Do NOT confuse it with "بدر". Always format as "عمان, شفا بدران".
    4. If an ad mentions being near or at a specific university, map the location directly to that university's region (e.g. "مادبا, الجامعة الألمانية الأردنية").
    
    Valid Regions List:
    {json.dumps(regions_list, ensure_ascii=False)}
    
    Ads:
    {json.dumps(ads_data, ensure_ascii=False)}
    
    Return ONLY a JSON array of objects with "ad_id" and "new_location".
    Example:
    [
        {{"ad_id": 123, "new_location": "عمان, دابوق"}},
        {{"ad_id": 124, "new_location": "إربد, الحصن"}}
    ]
    Do not return any markdown wrappers like ```json, just the raw JSON.
    """

    try:
        if _USE_NEW_SDK:
            client = _genai_new.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt,
                config={"temperature": 0.1}
            )
            raw = response.text.strip()
        else:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt, 
                generation_config=genai.types.GenerationConfig(temperature=0.1)
            )
            raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        updates = json.loads(raw.strip())
        return updates
    except Exception as e:
        log(f"Error calling AI: {e}")
        return None

def main():
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            log("Error: GOOGLE_API_KEY is missing.")
            return

    regions_list = get_all_regions()
    log(f"Found {len(regions_list)} valid regions.")

    db_init = SessionLocal()
    try:
        query = db_init.query(Ad.id).filter(
            or_(
                Ad.location.ilike('%other%'),
                Ad.location.ilike('%أخرى%'),
                Ad.location.ilike('%اخرى%'),
                Ad.location.ilike('%غير محدد%')
            )
        )
        ad_ids = [r[0] for r in query.all()]
    finally:
        db_init.close()
        
    log(f"Found {len(ad_ids)} ads remaining to process.")
    
    batch_size = 20
    success_count = 0
    fail_count = 0

    for i, batch_ids in enumerate(chunk_list(ad_ids, batch_size)):
        log(f"Processing batch {i+1} ({len(batch_ids)} ads)...")
        
        # 1. Fetch data with a very short-lived session
        db = SessionLocal()
        try:
            ads = db.query(Ad).filter(Ad.id.in_(batch_ids)).all()
            ads_data = []
            for ad in ads:
                ads_data.append({
                    "ad_id": ad.id,
                    "title": ad.title,
                    "description": ad.description or "",
                    "raw_description": ad.raw_description or "",
                    "current_location": ad.location
                })
        finally:
            db.close()
            
        # 2. Long running AI task (No active DB connection)
        updates = process_ads_batch(ads_data, regions_list, api_key)
        
        # 3. Update DB with a new short-lived session
        if updates:
            update_map = {item['ad_id']: item['new_location'] for item in updates if 'ad_id' in item and 'new_location' in item}
            
            db2 = SessionLocal()
            try:
                ads_to_update = db2.query(Ad).filter(Ad.id.in_(batch_ids)).all()
                for ad in ads_to_update:
                    if ad.id in update_map:
                        new_loc = update_map[ad.id]
                        new_loc = update_map[ad.id]
                        if new_loc != ad.location and new_loc != "" and "other" not in new_loc.lower() and "أخرى" not in new_loc:
                            if new_loc in regions_list:
                                ad.location = new_loc
                                success_count += 1
                            elif "," in new_loc:
                                # DYNAMIC REGION ADDITION
                                parts = [p.strip() for p in new_loc.split(",", 1)]
                                if len(parts) == 2:
                                    city_name, region_name = parts
                                    if region_name and region_name != "أخرى" and region_name.lower() != "other":
                                        city_obj = db2.query(City).filter(City.name_ar == city_name).first()
                                        if city_obj:
                                            existing_region = db2.query(Region).filter(
                                                Region.city_id == city_obj.id,
                                                Region.name_ar == region_name
                                            ).first()
                                            if not existing_region:
                                                try:
                                                    new_region = Region(
                                                        city_id=city_obj.id,
                                                        name_ar=region_name,
                                                        name_en=region_name
                                                    )
                                                    db2.add(new_region)
                                                    db2.flush()
                                                    log(f"    Dynamically added new region '{region_name}' to city '{city_name}'")
                                                except Exception as e:
                                                    log(f"    Failed to add dynamic region: {e}")
                                                    continue
                                            ad.location = new_loc
                                            success_count += 1
                
                db2.commit()
                log(f"  Batch {i+1} committed. Total successes so far: {success_count}")
            except Exception as e:
                log(f"  Unhandled error in batch {i+1} during commit: {e}")
                fail_count += len(batch_ids)
            finally:
                db2.close()
        else:
            log(f"  Batch {i+1} failed.")
            fail_count += len(batch_ids)
            
        time.sleep(2)

    log(f"Finished processing. Successfully updated {success_count} ads. Failed to process/update {fail_count} ads.")

if __name__ == "__main__":
    # Clear log file on startup
    with open("fix_locations_log.txt", "w", encoding="utf-8") as f:
        f.write("Starting location fix process...\n")
        
    try:
        main()
    except Exception as e:
        log(f"Unhandled exception: {e}")

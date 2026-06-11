import os
import time
from database import SessionLocal
import models
import google.generativeai as genai
from categorize_ads import AdCategoryUpdate

import sys
from dotenv import load_dotenv
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

gemini_api_key = os.getenv("GEMINI_API_KEY")

def run():
    db = SessionLocal()
    if not gemini_api_key:
        print("ERROR: API_KEY is not set.")
        return

    genai.configure(api_key=gemini_api_key)

    # 1. Fetch all categories and format them for the prompt
    print("Fetching categories from database...")
    db_categories = db.query(models.Category).all()
    parent_ids = {c.parent_id for c in db_categories if c.parent_id is not None}
    
    categories_context_lines = []
    for cat in db_categories:
        if cat.id in parent_ids:
            continue # Skip parent categories
            
        parent_name = ""
        if cat.parent_id:
            parent = next((p for p in db_categories if p.id == cat.parent_id), None)
            if parent:
                parent_name = f"{parent.name} > "
        
        linked_tags_str = ", ".join([tag.name for tag in getattr(cat, 'linked_tags', [])]) if getattr(cat, 'linked_tags', []) else ""
        tags = f" | Tag: {cat.tag}" if cat.tag else ""
        keywords = f" | Keywords: {linked_tags_str}" if linked_tags_str else ""
        categories_context_lines.append(f"ID: {cat.id} | Name: {parent_name}{cat.name}{tags}{keywords}")
        
    categories_context = "\n".join(categories_context_lines)
    print(f"Loaded {len(db_categories)} categories, keeping {len(categories_context_lines)} leaf categories.")

    # 2. Fetch ads that are currently assigned to parent categories!
    print("Fetching ads assigned to parent categories...")
    # parent_ids list from above
    ads_to_process = db.query(models.Ad).filter(models.Ad.category_id.in_(list(parent_ids))).all()
    print(f"Found {len(ads_to_process)} total ads in parent categories.")

    if not ads_to_process:
        print("No ads to fix!")
        return

    system_instruction = (
        "You are an expert AI categorization assistant specialized in Jordanian classifieds.\n"
        "You will receive an array of ads from the database.\n"
        "Your job is to read the ad text and map it to the PERFECT category ID from the provided list, and generate an array of descriptive 'suggested_tags'.\n"
        "Always try to use the MOST SPECIFIC sub-category (e.g. 'شقق للبيع' instead of just 'عقارات').\n\n"
        "Here are the available categories:\n"
        f"--- CATEGORIES LIST ---\n{categories_context}\n-----------------------\n\n"
        "For each ad, output its original `ad_id`, the best matching `category_id`, `suggested_tags` array, and carefully extract ALL possible fields into the `attributes` object."
    )

    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
    
    batch_size = 20
    processed_count = 0
    updated_count = 0

    for i in range(0, len(ads_to_process), batch_size):
        batch = ads_to_process[i:i+batch_size]
        prompts_array = []
        
        for ad in batch:
            text = ad.raw_description if ad.raw_description else ad.description
            if not text:
                text = ad.title
            prompts_array.append(f"Ad ID {ad.id}:\nTEXT: {text[:500]}")
            
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
                raw_json = raw_json[7:-3]
            elif raw_json.startswith("```"):
                raw_json = raw_json[3:-3]
                    
            extracted_updates = json.loads(raw_json.strip())
            
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
                        
                    new_attrs = update.get("attributes", {})
                    if new_attrs:
                        current_attrs = db_ad.attributes or {}
                        merged_attrs = dict(current_attrs)
                        for k, v in new_attrs.items():
                            if v is not None and (not isinstance(v, list) or len(v) > 0):
                                merged_attrs[k] = v
                        db_ad.attributes = merged_attrs
                        dirty = True
                    
                    if isinstance(suggested_tags, list) and len(suggested_tags) > 0:
                        unique_tags = list(set(suggested_tags))
                        for tag_name in unique_tags:
                            if not isinstance(tag_name, str): continue
                            clean_tag = tag_name.strip()
                            if not clean_tag: continue
                                
                            tag = db.query(models.Tag).filter(models.Tag.name == clean_tag).first()
                            if not tag:
                                tag = models.Tag(name=clean_tag)
                                db.add(tag)
                                db.commit()
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
            time.sleep(2)
            
        except Exception as e:
            print(f"ERROR on batch {i//batch_size + 1}: {e}")
            db.rollback()
            time.sleep(5)
            
    db.close()
    print(f"\nDONE! Re-mapped {updated_count} ads in the database.")

if __name__ == "__main__":
    run()

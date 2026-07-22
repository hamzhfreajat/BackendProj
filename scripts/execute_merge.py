import json
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

from database import SessionLocal
from models import Region, AdSearchIndex, Ad

def execute():
    plan_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'merge_plan.json')
    if not os.path.exists(plan_path):
        print("Merge plan not found.")
        return

    with open(plan_path, 'r', encoding='utf-8') as f:
        groups = json.load(f)

    db = SessionLocal()
    try:
        total_groups = len(groups)
        for i, group in enumerate(groups, 1):
            city_name = group['city']
            primary_id = group['primary']['id']
            primary_name = group['primary']['name']
            
            for dup in group['duplicates']:
                dup_id = dup['id']
                dup_name = dup['name']
                
                print(f"[{i}/{total_groups}] Merging dup_id {dup_id} into primary_id {primary_id}")
                
                # 1. Update AdSearchIndex
                db.query(AdSearchIndex).filter(AdSearchIndex.region_id == dup_id).update({"region_id": primary_id})
                
                # 2. Update Ads Location
                # The location format is "City, Region"
                old_loc = f"{city_name}, {dup_name}"
                new_loc = f"{city_name}, {primary_name}"
                
                ads_to_update = db.query(Ad).filter(Ad.location.ilike(f"{old_loc}%")).all()
                for ad in ads_to_update:
                    ad.location = ad.location.replace(old_loc, new_loc)
                    
                # 3. Delete Duplicate Region
                db.query(Region).filter(Region.id == dup_id).delete()
                
        db.commit()
        print("Successfully merged all duplicate regions and updated ads!")
    except Exception as e:
        db.rollback()
        print(f"Error during merge: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    execute()

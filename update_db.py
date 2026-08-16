import sys
sys.stdout.reconfigure(encoding='utf-8')
import io
import json
import glob
import os
import sys

# Setup DB session
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
from models import City, Region, Ad

db = SessionLocal()

def process_db():
    print("Parsing user_regions.txt...")
    city_map = {}
    current_city = None
    with io.open('user_regions.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # If line doesn't contain spaces and is in our known cities (or we can just query DB)
            # Or just assume headers are known cities
            city_in_db = db.query(City).filter(City.name_ar == line).first()
            if city_in_db:
                current_city = city_in_db
                city_map[current_city.id] = []
                print(f"Found City: {line}")
            elif current_city:
                city_map[current_city.id].append(line)
    
    # 1. Insert New Regions
    inserted_count = 0
    for city_id, regions in city_map.items():
        for reg_name in regions:
            # Check if exists
            exists = db.query(Region).filter(Region.city_id == city_id, Region.name_ar == reg_name).first()
            if not exists:
                new_reg = Region(name_ar=reg_name, name_en=reg_name, city_id=city_id)
                db.add(new_reg)
                inserted_count += 1
    
    db.commit()
    print(f"Inserted {inserted_count} new regions.")
    
    # 2. Delete مجمع الشمال from Irbid
    irbid = db.query(City).filter(City.name_ar == 'إربد').first()
    if irbid:
        majma = db.query(Region).filter(Region.city_id == irbid.id, Region.name_ar == 'مجمع الشمال').first()
        if majma:
            db.delete(majma)
            db.commit()
            print("Deleted 'مجمع الشمال' from Irbid.")
        else:
            print("'مجمع الشمال' not found in Irbid.")

    # 3. Compile all mappings from ai_mapped_*.json
    print("Compiling all ad mappings...")
    final_ad_locations = {}
    
    with io.open('verified_missing_regions.json', 'r', encoding='utf-8') as f:
        verified_missing = json.load(f)
        
    for file in glob.glob('ai_mapped_*.json'):
        with io.open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for ad_id, info in data.items():
                status = info.get('status')
                loc = info.get('location')
                
                if status == 'mapped':
                    final_ad_locations[ad_id] = loc
                elif status == 'missing' and loc in verified_missing:
                    # It might be INVALID
                    if verified_missing[loc] != 'INVALID':
                        final_ad_locations[ad_id] = verified_missing[loc]
                # Also apply the standardized Aqaba names for previously mapped regions if needed
                # (actually `verified_missing_regions.json` handles the new missing ones, 
                # but if an old one was mapped to 'التاسعة' somehow... wait, valid_locations didn't have 'التاسعة' so it was marked missing and got caught!)

    # 4. Update the Ads in the database
    updated_ads = 0
    not_found = 0
    
    # We load all ads from `أخرى` or we can just update by ID
    for ad_id_str, new_loc in final_ad_locations.items():
        try:
            ad_id = int(ad_id_str)
        except ValueError:
            continue
            
        ad = db.query(Ad).filter(Ad.id == ad_id).first()
        if ad:
            # We don't change location format, we expect "City, Region" but actually in db it's stored as "City, Region" string for now?
            # Wait, looking at the schema, Ad.location is a string.
            ad.location = new_loc
            updated_ads += 1
        else:
            not_found += 1
            
        if updated_ads % 100 == 0:
            db.commit()
            
    db.commit()
    print(f"Updated location for {updated_ads} ads.")
    print(f"Ads not found: {not_found}")

if __name__ == '__main__':
    process_db()

import os
from database import SessionLocal
from models import Ad, City, Region
from sqlalchemy import or_

db = SessionLocal()
try:
    aqaba = db.query(City).filter(City.name_ar == "العقبة").first()
    if not aqaba:
        print("Aqaba city not found!")
        exit()

    # Check if region already exists
    beach_region = db.query(Region).filter(
        Region.city_id == aqaba.id,
        Region.name_ar == "قرب الشاطئ"
    ).first()

    if not beach_region:
        beach_region = Region(
            city_id=aqaba.id,
            name_ar="قرب الشاطئ",
            name_en="Near the Beach"
        )
        db.add(beach_region)
        db.commit()
        print("Created new region near the beach")
    else:
        print("Region already exists")

    target_loc = "العقبة, قرب الشاطئ"

    # Find ads that should belong here (either location is exactly this, or contains 'قرب الشاطئ' and 'العقبة')
    # Or ads in "Others" that mention "قرب الشاطئ"
    ads_to_update = db.query(Ad).filter(
        or_(
            Ad.location == "العقبة, قرب الشاطئ",
            Ad.location == "قرب الشاطئ",
            Ad.location.like("%العقبة%أخرى%"),
            Ad.location.like("%other%"),
            Ad.location.like("%اخرى%")
        )
    ).all()

    count = 0
    for ad in ads_to_update:
        if ad.location == target_loc:
            continue # already correct
            
        desc = (ad.description or "") + " " + (ad.raw_description or "") + " " + (ad.title or "")
        if "قرب الشاطئ" in desc or "الشاطئ" in desc:
            # We want to be careful not to move things just for "الشاطئ" unless it's in Aqaba
            if "عقبة" in desc or "العقبة" in desc or ad.location == "العقبة, أخرى":
                ad.location = target_loc
                count += 1

    db.commit()
    print(f"Moved {count} ads to target loc")
    
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()

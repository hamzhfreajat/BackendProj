import os
from database import SessionLocal
from models import Ad, City, Region
import logging

logging.basicConfig(level=logging.INFO)

db = SessionLocal()
try:
    amman = db.query(City).filter(City.name_ar == "عمان").first()
    if not amman:
        print("Amman not found!")
        exit()

    # Find the wrong regions in Amman
    wrong_regions = db.query(Region).filter(
        Region.city_id == amman.id,
        Region.name_ar.in_([
            "العاشرة", "التاسعة – جمعيات", "العاشرة الشرقي", "العاشرة الشرقية", "العاشرة الغربي", "التاسعة"
        ])
    ).all()
    
    print(f"Found {len(wrong_regions)} wrongly added regions in Amman.")

    for wr in wrong_regions:
        name_ar = wr.name_ar
        print(f"Processing wrong region ID: {wr.id}")
        # Determine correct Aqaba region
        if "تاسعة" in name_ar or "التاسعة" in name_ar:
            correct_loc = "العقبة, السكنية 9"
        elif "عاشرة" in name_ar or "العاشرة" in name_ar:
            correct_loc = "العقبة, السكنية 10"
        else:
            continue
            
        # Update ads
        wrong_loc_str = f"عمان, {name_ar}"
        ads_to_fix = db.query(Ad).filter(Ad.location == wrong_loc_str).all()
        print(f"  Found {len(ads_to_fix)} ads in this wrong region.")
        for ad in ads_to_fix:
            ad.location = correct_loc
        
        # Delete the wrong region
        db.delete(wr)
        
    db.commit()
    print("Database fix committed.")
    
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()

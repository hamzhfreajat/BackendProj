import os
from database import SessionLocal
from models import City, Region, Ad

db = SessionLocal()
try:
    capital = db.query(City).filter(City.name_ar == "العاصمة").first()
    amman = db.query(City).filter(City.name_ar == "عمان").first()
    
    if capital and amman:
        print(f"Found capital (ID {capital.id}) and amman (ID {amman.id})")
        
        # move regions
        regions = db.query(Region).filter(Region.city_id == capital.id).all()
        print(f"Moving {len(regions)} regions to Amman...")
        for r in regions:
            r.city_id = amman.id
            
        db.delete(capital)
        db.commit()
        print("Done deleting capital city entry!")
    else:
        print("Not both found.")
        
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()

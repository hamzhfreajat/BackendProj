import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

# Mapping of City Name -> List of (name_ar, name_en) to add
new_regions_map = {
    "عمان": [("العبدلي", "Al Abdali"), ("زهران", "Zahran"), ("خريبة السوق", "Khreibet Es-Souq")],
    "إربد": [("الرمثا", "Ar Ramtha"), ("الطرة", "At Turra"), ("حوارة", "Hawara")],
    "العقبة": [("الديسة", "Ad Disah"), ("وادي عربة", "Wadi Araba")],
    "الكرك": [("غور المزرعة", "Ghor Al Mazra'a")],
    "البلقاء": [("البحر الميت", "Dead Sea")],
    "مادبا": [("البحر الميت", "Dead Sea")]
}

for city_name, regions in new_regions_map.items():
    # Find city
    city = db.query(models.City).filter(models.City.name_ar == city_name).first()
    if not city:
        print(f"Error: City '{city_name}' not found in the database!")
        continue
    
    for r_name_ar, r_name_en in regions:
        # Check if region already exists
        existing = db.query(models.Region).filter(
            models.Region.city_id == city.id,
            models.Region.name_ar == r_name_ar
        ).first()
        
        if existing:
            print(f"Region '{r_name_ar}' already exists in {city_name}.")
        else:
            new_reg = models.Region(city_id=city.id, name_ar=r_name_ar, name_en=r_name_en)
            db.add(new_reg)
            db.commit()
            print(f"SUCCESS: Inserted '{r_name_ar}' into {city_name} (City ID: {city.id}, New Region ID: {new_reg.id})")

print("All missing regions processed.")

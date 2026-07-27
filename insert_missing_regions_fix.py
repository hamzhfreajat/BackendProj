import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

new_regions_map = {
    "عمان": [("العبدلي", "Al Abdali"), ("زهران", "Zahran"), ("خريبة السوق", "Khreibet Es-Souq")],
    "إربد": [("الرمثا", "Ar Ramtha"), ("الطرة", "At Turra"), ("حوارة", "Hawara")],
    "العقبة": [("الديسة", "Ad Disah"), ("وادي عربة", "Wadi Araba")],
    "الكرك": [("غور المزرعة", "Ghor Al Mazra'a")],
    "البلقاء": [("البحر الميت", "Dead Sea")],
    "مادبا": [("البحر الميت", "Dead Sea")]
}

for city_name, regions in new_regions_map.items():
    city = db.query(models.City).filter(models.City.name_ar == city_name).first()
    if not city:
        continue
    
    for r_name_ar, r_name_en in regions:
        existing = db.query(models.Region).filter(
            models.Region.city_id == city.id,
            models.Region.name_ar == r_name_ar
        ).first()
        
        if not existing:
            new_reg = models.Region(city_id=city.id, name_ar=r_name_ar, name_en=r_name_en)
            db.add(new_reg)
            db.commit()

print("Success")

import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

bad_reg = db.query(models.Region).filter(models.Region.id == 1601).first()
if bad_reg:
    correct_reg = db.query(models.Region).filter(models.Region.id == 1722).first()
    city = db.query(models.City).filter(models.City.id == correct_reg.city_id).first()
    correct_full_name = f"{city.name_ar}, {correct_reg.name_ar}"
    
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_reg.name_ar}%")).all()
    for ad in ads:
        ad.location = correct_full_name
        
    db.delete(bad_reg)
    db.commit()
    print("Fixed 1601")
else:
    print("1601 not found")

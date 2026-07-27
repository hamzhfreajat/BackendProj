import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

merges = [
    (145, "جاوا", [(1704, "جاوة")])
]

for keep_id, keep_name, bad_list in merges:
    keep_reg = db.query(models.Region).filter(models.Region.id == keep_id).first()
    if not keep_reg:
        continue
        
    city = db.query(models.City).filter(models.City.id == keep_reg.city_id).first()
    keep_full_name = f"{city.name_ar}, {keep_reg.name_ar}"
    
    for bad_id, bad_name in bad_list:
        bad_reg = db.query(models.Region).filter(models.Region.id == bad_id).first()
        if bad_reg:
            ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_reg.name_ar}%")).all()
            for ad in ads:
                ad.location = keep_full_name
            db.delete(bad_reg)
        
        existing_alias = db.query(models.RegionAlias).filter(models.RegionAlias.alias_name == bad_name).first()
        if not existing_alias:
            alias = models.RegionAlias(region_id=keep_id, alias_name=bad_name)
            db.add(alias)

db.commit()
print("Success")

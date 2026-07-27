import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

to_remove = [1680, 1687, 1864, 236, 1706, 1732]

for rid in to_remove:
    reg = db.query(models.Region).filter(models.Region.id == rid).first()
    if reg:
        city = db.query(models.City).filter(models.City.id == reg.city_id).first()
        city_name = city.name_ar if city else ""
        ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{reg.name_ar}%")).all()
        for ad in ads:
            ad.location = city_name
        db.delete(reg)

to_merge = [
    (1601, "????? ??????", "????? ?????"),
    (1741, "?????", "???????"),
    (1817, "??? ?????????", "??? ????????"),
    (1671, "????????", "?? ???????"),
    (1519, "????????", "??????? ???????")
]

for bad_id, keep_name, bad_name in to_merge:
    bad_reg = db.query(models.Region).filter(models.Region.id == bad_id).first()
    if not bad_reg:
        continue
    correct_reg = db.query(models.Region).filter(models.Region.name_ar == keep_name).first()
    if not correct_reg:
        continue
    city = db.query(models.City).filter(models.City.id == correct_reg.city_id).first()
    correct_full_name = f"{city.name_ar}, {correct_reg.name_ar}"
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_name}%")).all()
    for ad in ads:
        ad.location = correct_full_name
    db.delete(bad_reg)

db.commit()
print("Success!")

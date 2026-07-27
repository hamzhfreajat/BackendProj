import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

junk_ids = [1891, 1537, 1626, 1649, 1711, 1734, 1831, 1501, 1686, 1538, 1647, 1506, 1499, 1679]

for bad_id in junk_ids:
    bad_reg = db.query(models.Region).filter(models.Region.id == bad_id).first()
    if not bad_reg:
        print(f"Region {bad_id} already deleted or not found.")
        continue
        
    city = db.query(models.City).filter(models.City.id == bad_reg.city_id).first()
    
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_reg.name_ar}%")).all()
    for ad in ads:
        # Just reset the location to the City name, since the region was garbage
        ad.location = city.name_ar if city else ""
        
    db.delete(bad_reg)

db.commit()
print("Success")

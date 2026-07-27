import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

merges = [
    (1915, "أبو علندا", [(1758, "ابو علندا")]),
    (1628, "إيدون", [(284, "ايدون")]),
    (1913, "البنيّات", [(27, "البنيات")]),
    (622, "عين والمعمرية", [(1914, "عين والمعمريه")]),
    (599, "أم بطيمة", [(131, "ام بطمه"), (1916, "أم بطيمة")]),
    (1754, "زيزيا", [(1923, "زويزيا"), (180, "زويزا")]),
    (1720, "أم زويتينة", [(1921, "أم زيتونة")]),
    (422, "الضليل", [(1909, "الظليل")]),
    (362, "ضاحية الأمير راشد", [(1912, "ضاحية الأمير راشد")]),
    (1651, "عربيلا مول", [(1626, "قرب أرابيلا مول")])
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

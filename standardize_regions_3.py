import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

# 1. Al-Nakhil
# Amman: merge 1904 into 205
bad_1904 = db.query(models.Region).filter(models.Region.id == 1904).first()
keep_205 = db.query(models.Region).filter(models.Region.id == 205).first()
if bad_1904 and keep_205:
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_1904.name_ar}%")).all()
    city = db.query(models.City).filter(models.City.id == keep_205.city_id).first()
    for ad in ads:
        if "عمان" in ad.location:  # only replace for Amman
            ad.location = ad.location.replace('عمان, النخيل', f'{city.name_ar}, {keep_205.name_ar}')
    db.delete(bad_1904)
    # alias
    if not db.query(models.RegionAlias).filter(models.RegionAlias.alias_name == "النخيل", models.RegionAlias.region_id == 205).first():
        db.add(models.RegionAlias(region_id=205, alias_name="النخيل"))

# Aqaba: rename 559 to 'حي النخيل'
reg_559 = db.query(models.Region).filter(models.Region.id == 559).first()
if reg_559:
    # Update ads
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{reg_559.name_ar}%")).all()
    for ad in ads:
        if 'العقبة, النخيل' in ad.location:
            ad.location = ad.location.replace('العقبة, النخيل', 'العقبة, حي النخيل')
    reg_559.name_ar = 'حي النخيل'

# 2. Al-Rimal
# Amman: merge 1907 to Aqaba's 539
bad_1907 = db.query(models.Region).filter(models.Region.id == 1907).first()
keep_539 = db.query(models.Region).filter(models.Region.id == 539).first()
if bad_1907 and keep_539:
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_1907.name_ar}%")).all()
    city = db.query(models.City).filter(models.City.id == keep_539.city_id).first()
    for ad in ads:
        if 'عمان, الرمال' in ad.location:
            ad.location = ad.location.replace('عمان, الرمال', f'{city.name_ar}, {keep_539.name_ar}')
    db.delete(bad_1907)

# 3. Al-Tas'ah
# Aqaba: merge 1901 to 1830
bad_1901 = db.query(models.Region).filter(models.Region.id == 1901).first()
keep_1830 = db.query(models.Region).filter(models.Region.id == 1830).first()
if bad_1901 and keep_1830:
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_1901.name_ar}%")).all()
    city = db.query(models.City).filter(models.City.id == keep_1830.city_id).first()
    for ad in ads:
        ad.location = ad.location.replace(f'العقبة, {bad_1901.name_ar}', f'{city.name_ar}, {keep_1830.name_ar}')
    db.delete(bad_1901)
    if not db.query(models.RegionAlias).filter(models.RegionAlias.alias_name == "التاسعة", models.RegionAlias.region_id == 1830).first():
        db.add(models.RegionAlias(region_id=1830, alias_name="التاسعة"))

# Amman: merge 1898 to 1830
bad_1898 = db.query(models.Region).filter(models.Region.id == 1898).first()
if bad_1898 and keep_1830:
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{bad_1898.name_ar}%")).all()
    city = db.query(models.City).filter(models.City.id == keep_1830.city_id).first()
    for ad in ads:
        ad.location = ad.location.replace(f'عمان, {bad_1898.name_ar}', f'{city.name_ar}, {keep_1830.name_ar}')
    db.delete(bad_1898)

# 4. Al-Mamoonyah (Madaba)
reg_1917 = db.query(models.Region).filter(models.Region.id == 1917).first()
if reg_1917:
    reg_1917.name_ar = 'المأمونية الشرقية'

reg_1924 = db.query(models.Region).filter(models.Region.id == 1924).first()
if reg_1924:
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{reg_1924.name_ar}%")).all()
    for ad in ads:
        ad.location = ad.location.replace(reg_1924.name_ar, 'المأمونية الغربية')
    reg_1924.name_ar = 'المأمونية الغربية'

# 5. Al-Mahdoud (Aqaba)
reg_553 = db.query(models.Region).filter(models.Region.id == 553).first()
if reg_553:
    ads = db.query(models.Ad).filter(models.Ad.location.like(f"%{reg_553.name_ar}%")).all()
    for ad in ads:
        ad.location = ad.location.replace(reg_553.name_ar, 'المحدود الشرقي')
    reg_553.name_ar = 'المحدود الشرقي'

db.commit()
print("Success")

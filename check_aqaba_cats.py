import os
from database import SessionLocal
from models import Ad, Category
from sqlalchemy import func

db = SessionLocal()
try:
    ads = db.query(Ad.category_id, Category.name, func.count(Ad.id)).join(Category, Ad.category_id == Category.id).filter(Ad.location.ilike('العقبة, أخرى%')).group_by(Ad.category_id, Category.name).all()
    with open('aqaba_ads_cat.txt', 'w', encoding='utf-8') as f:
        for cat_id, cat_name, count in ads:
            f.write(f"Category {cat_name} (ID {cat_id}): {count}\n")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

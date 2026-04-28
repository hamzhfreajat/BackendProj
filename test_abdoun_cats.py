import os
import sys
from database import SessionLocal
from models import Ad, Category
from sqlalchemy import func

sys.stdout.reconfigure(encoding='utf-8')

db = SessionLocal()
try:
    ads = db.query(Ad.category_id, Category.name, func.count(Ad.id)).join(Category, Ad.category_id == Category.id).filter(Ad.location.like('عمان, عبدون%')).group_by(Ad.category_id, Category.name).all()
    for cat_id, cat_name, count in ads:
        print(f"Category {cat_name} (ID {cat_id}): {count}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

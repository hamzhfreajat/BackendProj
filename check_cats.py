from database import SessionLocal
from models import Category

db = SessionLocal()
cats = db.query(Category).filter(Category.id.in_([10, 12])).all()
with open('cat_check.txt', 'w', encoding='utf-8') as f:
    for c in cats:
        f.write(f"ID: {c.id} | Name: {c.name}\n")
db.close()

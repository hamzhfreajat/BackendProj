import logging
logging.basicConfig(level=logging.ERROR)
from database import SessionLocal
from models import Category
db = SessionLocal()
cats = db.query(Category).all()
with open('cats.txt', 'w', encoding='utf-8') as f:
    for c in cats:
        if c.parent_id is None or c.parent_id in [1, 2, 3]:
            f.write(f"{c.id}: {c.name} (parent: {c.parent_id})\n")

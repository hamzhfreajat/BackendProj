import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from database import SessionLocal
from models import Category

db = SessionLocal()
orphan_cats = db.query(Category).filter(Category.id >= 6976, Category.id <= 7050).all()
for c in orphan_cats:
    print(f"ID: {c.id}, Name: {c.name}, ParentID: {c.parent_id}")


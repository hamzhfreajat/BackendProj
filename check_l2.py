from database import SessionLocal
from models import Category
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db = SessionLocal()

for check_id in [1001, 100101, 10010101]:
    c = db.query(Category).filter_by(id=check_id).first()
    if c:
        print(f"ID: {c.id}, Name: {c.name}, ParentID: {c.parent_id}")
    else:
        print(f"{check_id} not in DB!")

db.close()

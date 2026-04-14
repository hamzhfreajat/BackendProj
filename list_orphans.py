from database import SessionLocal
from models import Category

db = SessionLocal()
orphans = db.query(Category).filter(Category.parent_id == None, Category.id > 1000).all()

count = 0
for o in orphans:
    print(f"{o.id} | {o.name}")
    count += 1

print(f"Total orphans found: {count}")
db.close()

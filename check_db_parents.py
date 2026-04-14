from database import SessionLocal
from models import Category

db = SessionLocal()

c = db.query(Category).filter_by(id=10010101).first()
if c:
    print(f"ID: {c.id}, Name: {c.name}, ParentID: {c.parent_id}")
else:
    print("10010101 Not found")

# Check all with parent_id=None
roots = db.query(Category).filter(Category.parent_id == None).all()
print(f"Roots count: {len(roots)}")
print("Roots:")
for r in roots[:50]:
    print(f" - ID: {r.id}, Name: {r.name}")

db.close()

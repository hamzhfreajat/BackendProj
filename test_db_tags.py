import sys
from database import SessionLocal
from models import Category, Tag, category_tags

db = SessionLocal()
cat = db.query(Category).filter(Category.name.like('%عقارات للإيجار%')).first()
if not cat:
    print("Category not found")
    sys.exit(1)

print(f"Category: {cat.name} (ID: {cat.id})")
for t in cat.linked_tags:
    print(t.name)

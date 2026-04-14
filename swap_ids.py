from database import SessionLocal
from models import Category
import re

db = SessionLocal()
# Delete all children of 12 (Pets) that were wrongly created
old_pets = db.query(Category).filter(Category.id >= 1200, Category.id < 130000000).all()
for c in old_pets:
    db.delete(c)
    
db.commit()

# Delete id 10 and 12 temporarily so seed can recreate them cleanly
cat10 = db.query(Category).filter_by(id=10).first()
cat12 = db.query(Category).filter_by(id=12).first()
if cat10:
    db.delete(cat10)
if cat12:
    db.delete(cat12)
db.commit()

db.close()
print("Cleaned up database nodes for 10 and 12.")

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 10 with 12 for Fashion
content = content.replace(
    '(10, None, "أزياء وجمال"',
    '(12, None, "أزياء وجمال"'
)

# And replace 12 with 10 for Pets
content = content.replace(
    '(12, None, "حيوانات أليفة"',
    '(10, None, "حيوانات أليفة"'
)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Swapped top-level IDs in seed_categories.py")

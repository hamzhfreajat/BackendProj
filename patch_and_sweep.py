from database import SessionLocal
from models import Category
import re

# 1. Fix big ints in seed_categories.py
with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('(120302020101,', '(12999001,')
content = content.replace('(120302020102,', '(12999002,')
content = content.replace('(120302020103,', '(12999003,')
content = content.replace('(120302020104,', '(12999004,')
content = content.replace('120302020101}', '12999001}')

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("seed_categories.py patched for BigInt overflow.")

# 2. Sweep database orphans
db = SessionLocal()
REAL_ROOTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

orphans = db.query(Category).filter(Category.parent_id == None, Category.id.notin_(REAL_ROOTS)).all()
print(f"Purging {len(orphans)} orphaned pseudo-roots...")
for o in orphans:
    db.delete(o)

db.commit()
db.close()
print("Orphans swept. Ready for accurate seeding.")

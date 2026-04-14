from database import SessionLocal
from models import Category
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db = SessionLocal()

print("--- Level 1 ---")
l1 = db.query(Category).filter(Category.id == 1001).first()
print(f"1001 (L1): {'FOUND' if l1 else 'MISSING'}, Parent: {l1.parent_id if l1 else 'N/A'}")

print("--- Level 2 ---")
l2 = db.query(Category).filter(Category.id == 100101).first()
print(f"100101 (L2): {'FOUND' if l2 else 'MISSING'}, Parent: {l2.parent_id if l2 else 'N/A'}")

print("--- Level 3 ---")
l3 = db.query(Category).filter(Category.id == 10010101).first()
print(f"10010101 (L3): {'FOUND' if l3 else 'MISSING'}, Parent: {l3.parent_id if l3 else 'N/A'}")

# Total categories mapped to ID 10 tree
pets_tree = db.query(Category).filter(Category.id >= 1000, Category.id < 1100000000).all()
print(f"Total nodes starting with 10xxx in DB: {len(pets_tree)}")

null_parents = [c.id for c in pets_tree if c.parent_id is None]
print(f"Total nodes starting with 10xxx with parent_id=None: {len(null_parents)}")

db.close()

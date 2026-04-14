from database import SessionLocal
from models import Category

db = SessionLocal()

brands_to_find = ['oppo', 'xiaomi', 'infinix', 'اوبو', 'شاومي', 'انفينيكس']

cats = db.query(Category).all()

found = []
for c in cats:
    name = (c.name or "").lower()
    slugs_str = str(c.slugs).lower()
    
    for b in brands_to_find:
        if b in name or b in slugs_str:
            found.append(f"ID: {c.id} | Parent: {c.parent_id} | Brand: {b} | Name: {c.name}")
            break

with open('brands_ids.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(found))
    
db.close()

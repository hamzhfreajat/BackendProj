import sys
from database import SessionLocal
from models import Category, Ad

db = SessionLocal()

ads = db.query(Ad).filter(Ad.category_id != None).all()
print(f"Checking {len(ads)} ads...")
updated = 0

for ad in ads:
    if not ad.linked_tags:
        continue
        
    dest_category = db.query(Category).filter(Category.id == ad.category_id).first()
    if not dest_category:
        continue
        
    for tag in ad.linked_tags:
        if tag not in dest_category.linked_tags:
            dest_category.linked_tags.append(tag)
            updated += 1

db.commit()
print(f"Successfully migrated {updated} tags to their parent categories globally!")

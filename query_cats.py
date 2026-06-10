import sys
sys.path.append('.')
from database import SessionLocal
import models
import json

from sqlalchemy import text
db = SessionLocal()
db.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS last_notified_ad_count INTEGER DEFAULT 0"))
db.commit()
cats = db.query(models.Category).all()

# Find parent of شقق للايجار
target = None
for c in cats:
    if "شقق للايجار" in c.name:
        target = c

with open('cat_output.txt', 'w', encoding='utf-8') as f:
    if target:
        f.write(f"Found {target.name} with ID {target.id}, parent {target.parent_id}\n")
        if target.parent_id:
            parent = db.query(models.Category).filter(models.Category.id == target.parent_id).first()
            if parent:
                f.write(f"Parent is {parent.name} with ID {parent.id}\n")
        
    sakani = None
    for c in cats:
        if "سكني" in c.name and c.parent_id == 3:
            sakani = c
            f.write(f"Found sakani: {c.name} with ID {c.id}, parent {c.parent_id}\n")

    if sakani:
        children = [c.name for c in cats if c.parent_id == sakani.id]
        f.write(f"Children of sakani: {children}\n")

db.close()

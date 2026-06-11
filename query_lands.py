import os
os.environ["PYTHONIOENCODING"] = "utf-8"
from database import SessionLocal
import models

db = SessionLocal()
with open("lands_cats.txt", "w", encoding="utf-8") as f:
    parent = db.query(models.Category).filter(models.Category.name == "أراضي للبيع").first()
    if parent:
        f.write(f"{parent.id}: {parent.name}\n")
        children = db.query(models.Category).filter(models.Category.parent_id == parent.id).all()
        for child in children:
            f.write(f"  {child.id}: {child.name}\n")
            grandchildren = db.query(models.Category).filter(models.Category.parent_id == child.id).all()
            for gc in grandchildren:
                f.write(f"    {gc.id}: {gc.name}\n")
    else:
        # Search for any 'أراضي'
        cats = db.query(models.Category).filter(models.Category.name.like('%أراضي%')).all()
        for c in cats:
            f.write(f"{c.id}: {c.name} (parent_id: {c.parent_id})\n")

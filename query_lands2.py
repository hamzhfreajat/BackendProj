import os
os.environ["PYTHONIOENCODING"] = "utf-8"
from database import SessionLocal
import models

db = SessionLocal()
with open("lands_cats2.txt", "w", encoding="utf-8") as f:
    parent = db.query(models.Category).filter(models.Category.id == 19000).first()
    if parent:
        f.write(f"{parent.id}: {parent.name}\n")
        children = db.query(models.Category).filter(models.Category.parent_id == parent.id).all()
        for child in children:
            f.write(f"  {child.id}: {child.name}\n")

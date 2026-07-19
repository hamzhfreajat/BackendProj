import os
from database import SessionLocal
import models
db = SessionLocal()
cats = db.query(models.Category).filter(models.Category.name_ar.like("%أراضي%")).all()
for c in cats:
    print(f"id={c.id}, parent_id={c.parent_id}, name_ar={c.name_ar}")
db.close()

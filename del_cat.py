import os
from database import SessionLocal
import models
db = SessionLocal()
try:
    cat = db.query(models.Category).filter(models.Category.id == 313).first()
    if cat:
        db.delete(cat)
        db.commit()
        print("Deleted category 313")
    else:
        print("Not found")
except Exception as e:
    print(f"Error: {e}")
db.close()

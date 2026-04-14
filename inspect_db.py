from database import SessionLocal
import models

db = SessionLocal()

print("Category 410:", db.query(models.Category).filter_by(id=410).first())
print("Category 4157:", db.query(models.Category).filter_by(id=4157).first())
print("Category 4201:", db.query(models.Category).filter_by(id=4201).first())

print("Count of categories:", db.query(models.Category).count())

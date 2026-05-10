import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from database import SessionLocal

db = SessionLocal()
try:
    cats = db.query(models.Category).all()
    for c in cats:
        print(f"ID: {c.id}, Name: {c.name_ar}, ParentID: {c.parent_id}")
finally:
    db.close()

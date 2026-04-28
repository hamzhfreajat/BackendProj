import os
from database import SessionLocal
from models import City

db = SessionLocal()
try:
    cities = db.query(City).all()
    for c in cities:
        if "محافظة" in c.name_ar or "عاصمة" in c.name_ar:
            print(f"Found: {c.id} - {c.name_ar.encode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

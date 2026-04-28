import os
import sys
from database import SessionLocal
from models import Ad

sys.stdout.reconfigure(encoding='utf-8')

db = SessionLocal()
try:
    locations = db.query(Ad.location).distinct().limit(20).all()
    for loc in locations:
        print(loc[0])
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

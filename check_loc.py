import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import SessionLocal
from models import City, Region

db = SessionLocal()
cities = db.query(City).limit(1).all()
for c in cities:
    print(f"City: {c.name_ar} (ID: {c.id})")
regions = db.query(Region).limit(2).all()
for r in regions:
    print(f"Region: {r.name_ar} (ID: {r.id}, City ID: {r.city_id})")

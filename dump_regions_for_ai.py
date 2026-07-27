import sys, os, json
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session
from collections import defaultdict

db: Session = SessionLocal()
regions = db.query(models.Region).all()

city_map = defaultdict(list)
for r in regions:
    city = db.query(models.City).filter(models.City.id == r.city_id).first()
    city_name = city.name_ar if city else "Unknown"
    city_map[city_name].append(r.name_ar)

out_path = r'C:\Users\hfraijat\.gemini\antigravity\brain\b5c78e29-59b6-45e8-ab63-050645670f8a\scratch\all_db_regions.json'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(city_map, f, ensure_ascii=False, indent=4)
    
print("Dumped regions successfully.")

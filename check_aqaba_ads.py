import os
from database import SessionLocal
from models import Ad
from sqlalchemy import func

db = SessionLocal()
try:
    ads = db.query(Ad.location, func.count(Ad.id)).filter(Ad.location.ilike('%العقبة%')).group_by(Ad.location).all()
    with open('aqaba_ads_out.txt', 'w', encoding='utf-8') as f:
        for loc, count in ads:
            f.write(f"{loc}: {count}\n")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

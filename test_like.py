import os
from database import SessionLocal
from models import Ad

db = SessionLocal()
try:
    print("Testing ILIKE:")
    ads_ilike = db.query(Ad).filter(Ad.location.ilike("عمان, أخرى%")).count()
    print(f"ILIKE Amman, Other count: {ads_ilike}")

    print("Testing LIKE:")
    ads_like = db.query(Ad).filter(Ad.location.like("عمان, أخرى%")).count()
    print(f"LIKE Amman, Other count: {ads_like}")
    
    print("Testing LIKE with English 'other':")
    ads_like_en = db.query(Ad).filter(Ad.location.like("عمان, other%")).count()
    print(f"LIKE Amman, other count: {ads_like_en}")
    
    print("Testing ILIKE with English 'other':")
    ads_ilike_en = db.query(Ad).filter(Ad.location.ilike("عمان, other%")).count()
    print(f"ILIKE Amman, other count: {ads_ilike_en}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

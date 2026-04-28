import os
from database import SessionLocal
from models import Ad

db = SessionLocal()
try:
    print("Testing LIKE Amman, Abdoun:")
    ads_abdoun = db.query(Ad).filter(Ad.location.like("عمان, عبدون%")).count()
    print(f"LIKE Amman, Abdoun count: {ads_abdoun}")
    
    print("Testing LIKE Amman, Khalda:")
    ads_khalda = db.query(Ad).filter(Ad.location.like("عمان, خلدا%")).count()
    print(f"LIKE Amman, Khalda count: {ads_khalda}")

    print("Testing ILIKE Amman, Abdoun:")
    ads_ilike_abdoun = db.query(Ad).filter(Ad.location.ilike("عمان, عبدون%")).count()
    print(f"ILIKE Amman, Abdoun count: {ads_ilike_abdoun}")
    
    print("Testing EXACT match Amman, Abdoun:")
    ads_exact = db.query(Ad).filter(Ad.location == "عمان, عبدون").count()
    print(f"Exact match count: {ads_exact}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

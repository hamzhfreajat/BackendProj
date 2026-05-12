from database import SessionLocal
import models

db = SessionLocal()
try:
    ad = db.query(models.Ad).filter(models.Ad.id == 7030).first()
    if ad:
        print(f"Ad 7030 found! Owner User ID: {ad.user_id}")
    else:
        print("Ad 7030 not found in database!")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

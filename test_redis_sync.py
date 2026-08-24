import sys
import os
import asyncio
from database import SessionLocal
import models
from sqlalchemy import update, func

def test_sync():
    db = SessionLocal()
    # Find an ad to test
    ad = db.query(models.Ad).first()
    if not ad:
        print("No ads found in DB")
        return
        
    print(f"Original views for ad {ad.id}: {ad.views}")
    
    # Simulate views_data from redis
    views_data = {str(ad.id).encode(): b'5'}
    
    try:
        for ad_id_str, count_str in views_data.items():
            ad_id = int(ad_id_str)
            count = int(count_str)
            if count > 0:
                stmt = update(models.Ad).where(models.Ad.id == ad_id).values(
                    views=func.coalesce(models.Ad.views, 0) + count
                )
                db.execute(stmt)
        db.commit()
        print("Update committed")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        
    # Check if updated
    db.refresh(ad)
    print(f"New views for ad {ad.id}: {ad.views}")
    db.close()

if __name__ == "__main__":
    test_sync()

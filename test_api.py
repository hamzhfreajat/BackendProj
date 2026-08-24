from fastapi.testclient import TestClient
from main import app, sync_ad_views_worker
import asyncio
from database import SessionLocal
import models
import schemas
from auth import redis_client

client = TestClient(app)

def run_test():
    db = SessionLocal()
    # Find an ad
    ad = db.query(models.Ad).first()
    if not ad:
        print("No ads found.")
        return
        
    print(f"Initial views: {ad.views}")
    
    # 1. Send bulk-views
    response = client.post("/api/ads/interactions/bulk-views", json={"ad_ids": [ad.id]})
    print(f"API response: {response.status_code} {response.json()}")
    
    # Check redis
    if redis_client:
        buffer = redis_client.hgetall("ad_views_buffer")
        print(f"Redis buffer: {buffer}")
        
    # 2. Run sync_ad_views_worker ONE iteration
    # Since it's an infinite loop, let's just copy the body of the loop
    if redis_client and redis_client.exists("ad_views_buffer"):
        pipe = redis_client.pipeline()
        pipe.hgetall("ad_views_buffer")
        pipe.delete("ad_views_buffer")
        results = pipe.execute()
        views_data = results[0]
        if views_data:
            from sqlalchemy import update, func
            for ad_id_str, count_str in views_data.items():
                db.execute(update(models.Ad).where(models.Ad.id == int(ad_id_str)).values(
                    views=func.coalesce(models.Ad.views, 0) + int(count_str)
                ))
            db.commit()
            print("Sync complete.")
            
    # Check DB again
    db.refresh(ad)
    print(f"Final views: {ad.views}")

if __name__ == "__main__":
    run_test()

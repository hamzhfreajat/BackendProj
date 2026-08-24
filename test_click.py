from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

client = TestClient(app)

def run_test():
    db = SessionLocal()
    # Find an ad
    ad = db.query(models.Ad).first()
    if not ad:
        print("No ads found.")
        return
        
    print(f"Initial views: {ad.views}")
    
    # Track click
    response = client.post(f"/api/ads/{ad.id}/track-click", json={"action_type": "call"})
    print(f"API response: {response.status_code} {response.json()}")
    
    # Check DB again
    db.refresh(ad)
    print(f"Final views: {ad.views}")

if __name__ == "__main__":
    run_test()

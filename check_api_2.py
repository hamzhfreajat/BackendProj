import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
import models
import schemas
from main import set_ad_bid
from fastapi import HTTPException

def test():
    db = SessionLocal()
    ad = db.query(models.Ad).first()
    if not ad:
        print("No ad found in database.")
        return
    user = db.query(models.User).filter(models.User.id == ad.user_id).first()

    print(f"Testing user ID: {user.id}, Phone: {user.phone}, Balance: {user.wallet_balance}")
    print(f"Testing ad ID: {ad.id}")

    try:
        bid_request = schemas.AdBidRequest(cpc_bid=0.1)
        result = set_ad_bid(ad.id, bid_request, current_user=user, db=db)
        print("Success! Ad bid updated to:", result.cpc_bid)
    except HTTPException as e:
        print("HTTPException raised:", e.status_code, e.detail)

if __name__ == "__main__":
    test()

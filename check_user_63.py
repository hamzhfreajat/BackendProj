import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
import models

def test():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.id == 63).first()
    if not user:
        print("User 63 not found.")
        return
    print(f"User 63 found! Email: {user.email}, Balance: {user.wallet_balance}")

if __name__ == "__main__":
    test()

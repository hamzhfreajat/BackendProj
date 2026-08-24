import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import SessionLocal
import models

def test():
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.id == 63).first()
    if not user:
        print("User not found.")
        return
        
    val = user.wallet_balance
    print(f"wallet_balance from DB is: {repr(val)} (type: {type(val)})")
    
    evaluated = float(val or 0)
    print(f"float(val or 0) is: {evaluated}")
    
    print(f"evaluated < 10.0 is: {evaluated < 10.0}")

if __name__ == "__main__":
    test()

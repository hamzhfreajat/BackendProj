import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

def main():
    db = SessionLocal()
    users = db.query(models.User).all()
    print("Users:")
    for u in users:
        print(f"ID: {u.id}, Email: {u.email}, Wallet: {u.wallet_balance}")
        
    transactions = db.query(models.WalletTransaction).all()
    print("\nTransactions:")
    for t in transactions:
        print(f"ID: {t.id}, User ID: {t.user_id}, Amount: {t.amount}, Type: {t.transaction_type}, Ref: {t.reference_id}")
    db.close()

if __name__ == "__main__":
    main()

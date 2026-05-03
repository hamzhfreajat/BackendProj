from database import SessionLocal
from models import User

def main():
    db = SessionLocal()
    try:
        names = {
            'user-15': 'عمر عبدالله',
            'user-16': 'خالد عبدالرحمن',
            'user-17': 'يوسف محمود',
            'user-18': 'طارق زياد',
            'user-19': 'سعيد حسن'
        }
        
        users = db.query(User).filter(User.username.in_(names.keys())).all()
        for u in users:
            u.full_name = names[u.username]
            print(f"Updated {u.username}")
            
        db.commit()
        print("Done!")
    finally:
        db.close()

if __name__ == "__main__":
    main()

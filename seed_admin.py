import sys
sys.path.append('d:/open/classifieds-app/backend')

from database import SessionLocal
import models
from auth import get_password_hash

def seed_users():
    db = SessionLocal()
    try:
        users_to_seed = [
            ("hamza", "123456789@Hf"),
            ("gafer", "123456789@Gf")
        ]
        
        for username, password in users_to_seed:
            user = db.query(models.User).filter(models.User.username == username).first()
            if not user:
                print(f"Creating user {username}...")
                user = models.User(
                    username=username,
                    hashed_password=get_password_hash(password),
                    user_type="admin",
                    is_identity_verified=True
                )
                db.add(user)
                db.commit()
                print(f"User {username} created successfully!")
            else:
                print(f"User {username} exists. Overriding password...")
                user.hashed_password = get_password_hash(password)
                user.user_type = "admin"
                db.commit()
                print(f"User {username} password reset successfully!")
                
        # Optional: Disable or delete the old default 'admin'
        old_admin = db.query(models.User).filter(models.User.username == "admin").first()
        if old_admin:
            print("Removing old default 'admin' user...")
            db.delete(old_admin)
            db.commit()
            
    except Exception as e:
        print(f"Error seeding users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()

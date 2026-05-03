from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User, Ad, SourceType

def main():
    db = SessionLocal()
    try:
        # Create 5 fake users
        fake_users = []
        for i in range(15, 20):
            mobile = f"07900000{i}"
            username = f"user-{i}"
            
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == username).first()
            
            if not existing_user:
                new_user = User(
                    username=username,
                    mobile_number=mobile,
                    phone=mobile,
                    user_type="private",
                    is_phone_verified=True,
                    is_identity_verified=True,
                    full_name=f"Fake User {i}",
                    hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq" # 123456
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                fake_users.append(new_user)
                print(f"Created {username} with mobile {mobile}")
            else:
                fake_users.append(existing_user)
                print(f"User {username} already exists")

        # Now find all scraper ads
        scraper_ads = db.query(Ad).filter(Ad.source_type.in_([SourceType.SCRAPER_BOT, SourceType.SCRAPER])).all()
        print(f"Found {len(scraper_ads)} scraper ads")
        
        # Distribute ads among fake users
        for i, ad in enumerate(scraper_ads):
            target_user = fake_users[i % len(fake_users)]
            ad.user_id = target_user.id
            ad.source_type = SourceType.ORGANIC_USER # Change to organic so UI works naturally
            # also update the attributes dictionary to have the user's phone number just in case
            attrs = ad.attributes.copy() if ad.attributes else {}
            attrs["phone_number"] = target_user.mobile_number
            ad.attributes = attrs
            
        db.commit()
        print(f"Successfully reassigned {len(scraper_ads)} ads to {len(fake_users)} fake users.")
    finally:
        db.close()

if __name__ == "__main__":
    main()

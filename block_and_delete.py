import os
from dotenv import load_dotenv

load_dotenv('d:/open/classifieds-app/backend/.env')

from sqlalchemy import create_engine, or_, text, cast, String
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'classifieds')
    db_port = os.getenv('DB_PORT', '5432')
    DATABASE_URL = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import sys
sys.path.append('d:/open/classifieds-app/backend')
import models

def execute_task():
    print("Creating table if not exists...")
    models.BlockedPhoneNumber.__table__.create(bind=engine, checkfirst=True)
    
    db = SessionLocal()
    phone = '0786688634'
    try:
        print(f"Finding ads with phone {phone}...")
        # Find ads directly via attributes
        ads_to_delete_json = db.query(models.Ad).filter(
            cast(models.Ad.attributes, String).ilike(f'%{phone}%')
        ).all()
        
        # Find ads via user
        ads_to_delete_user = db.query(models.Ad).outerjoin(
            models.User, models.Ad.user_id == models.User.id
        ).filter(
            or_(
                models.User.phone.ilike(f'%{phone}%'),
                models.User.mobile_number.ilike(f'%{phone}%')
            )
        ).all()
        
        all_ads_to_delete = {ad.id: ad for ad in ads_to_delete_json + ads_to_delete_user}.values()
        
        count = len(all_ads_to_delete)
        print(f"Found {count} ads to delete.")
        
        for ad in all_ads_to_delete:
            db.delete(ad)
            
        print("Ads deleted.")
        
        print(f"Adding {phone} to blocklist...")
        existing = db.query(models.BlockedPhoneNumber).filter_by(phone_number=phone).first()
        if not existing:
            new_block = models.BlockedPhoneNumber(phone_number=phone)
            db.add(new_block)
            print("Added to blocklist.")
        else:
            print("Already in blocklist.")
            
        db.commit()
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    execute_task()

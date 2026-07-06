
import os
import sys

with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Ad
from schemas import AdUpdate
from main import update_ad
from fastapi import BackgroundTasks

engine = create_engine(os.environ['DATABASE_URL'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

ad = db.query(Ad).filter(Ad.id == 14067).first()
if ad:
    class MockUser:
        id = ad.user_id
        user_type = 'user'
    
    update_data = AdUpdate(image_urls=['test1', 'test2', 'test3'])
    try:
        updated = update_ad(14067, update_data, BackgroundTasks(), MockUser(), db)
        print('Returned from update_ad:', updated.attributes.get('image_urls', []))
    except Exception as e:
        print('Error:', e)
    
    # Reload from DB in a new session to prove it saved
    db.commit()
    db.close()
    
    db2 = SessionLocal()
    ad2 = db2.query(Ad).filter(Ad.id == 14067).first()
    print('After reload:', ad2.attributes.get('image_urls', []))
    db2.close()


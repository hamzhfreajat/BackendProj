
import os
import sys

# Read env file
env_vars = {}
with open('.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ[k] = v

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Ad

engine = create_engine(os.environ['DATABASE_URL'])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

ad = db.query(Ad).filter(Ad.id == 14067).first()
if ad:
    print('Before:', ad.attributes.get('image_urls', []))
    
    attributes = ad.attributes.copy() if ad.attributes else {}
    attributes['image_urls'] = ['test1', 'test2', 'test3']
    
    setattr(ad, 'attributes', attributes)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(ad, 'attributes')
    
    db.commit()
    db.refresh(ad)
    print('After direct modify:', ad.attributes.get('image_urls', []))


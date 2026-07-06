import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Ad
from database import SessionLocal

session = SessionLocal()

ads = session.query(Ad).filter(Ad.location.like('%أخرى%')).all()

lines = []
for ad in ads:
    lines.append(f'CITY:{ad.location} | AD:{ad.description}')

with open('all_701_ads_flat.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Total ads written: {len(lines)}")

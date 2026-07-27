import sys, json
sys.path.append(r'd:\open\classifieds-app\backend')
from database import SessionLocal
import models
db = SessionLocal()

all_ads = db.query(models.Ad).filter(
    models.Ad.is_published == True,
    models.Ad.is_sold == False,
    models.Ad.is_rejected == False
).all()

from collections import Counter
regions = Counter()
for ad in all_ads:
    if ad.location:
        parts = [p.strip() for p in ad.location.split(',')]
        if len(parts) >= 2:
            regions[parts[1]] += 1

with open('regions_out.txt', 'w', encoding='utf-8') as f:
    for reg, count in regions.most_common(50):
        f.write(f'{reg}: {count}\n')

from database import SessionLocal
from models import Ad
from search_service import SearchService
import time

db = SessionLocal()
ads = db.query(Ad).filter(Ad.is_published == True).all()
print(f'Syncing {len(ads)} ads...')
for i, ad in enumerate(ads):
    SearchService.sync_ad_to_search_index(db, ad, commit=False)
    if i % 100 == 0:
        db.commit()
        print(f'Synced {i} ads')
db.commit()
print('Done!')

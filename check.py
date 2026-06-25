import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import SessionLocal
from models import Ad

db = SessionLocal()
ads = db.query(Ad).filter(Ad.location.ilike('%تلاع العلي%')).limit(5).all()
print(f"Found {len(ads)} ads using ilike on location.")
for ad in ads:
    print(f"Ad ID: {ad.id}, Location: {ad.location}, Attributes: {ad.attributes.get('region_id') if ad.attributes else None}")
    
# Let's also check if AdSearchIndex has region_id
from models import AdSearchIndex
si = db.query(AdSearchIndex).filter(AdSearchIndex.ad_id == (ads[0].id if ads else 0)).first()
if si:
    print(f"AdSearchIndex -> Ad ID: {si.ad_id}, City ID: {si.city_id}, Region ID: {si.region_id}")

import sys
sys.stdout.reconfigure(encoding='utf-8')
from database import SessionLocal
from models import Ad
import json

db = SessionLocal()
ads = db.query(Ad).filter(Ad.location.ilike('%تلاع العلي%')).limit(10).all()

image_urls = []
for ad in ads:
    if hasattr(ad, 'image_urls') and ad.image_urls:
        image_urls.extend(ad.image_urls)
    elif hasattr(ad, 'image_url') and ad.image_url:
        try:
            parsed = json.loads(ad.image_url)
            if isinstance(parsed, list):
                image_urls.extend(parsed)
            else:
                image_urls.append(ad.image_url)
        except Exception as e:
            image_urls.append(ad.image_url)
        
image_urls = [url for url in image_urls if url and isinstance(url, str)][:10]
print("Extracted images:", len(image_urls))
for url in image_urls:
    print(url)

import sys
sys.path.append('d:\\open\\classifieds-app\\backend')

from database import SessionLocal
from sqlalchemy import text
import json

db = SessionLocal()

sql = "SELECT title, description FROM ads WHERE is_published = true LIMIT 300"
ads = db.execute(text(sql)).fetchall()

out = []
for ad in ads:
    out.append({"title": ad.title, "description": ad.description[:200] if ad.description else ""})

with open('sample_ads.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

db.close()

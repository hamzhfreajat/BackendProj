import sys
import json
from database import SessionLocal
from sqlalchemy import text
import models

db = SessionLocal()

cats = db.query(models.Category).filter(models.Category.name.ilike('%??? ???????%')).all()
cat_ids = [c.id for c in cats]

count_raw = db.query(models.Ad).filter(
    models.Ad.is_published == True,
    models.Ad.category_id.in_(cat_ids),
    models.Ad.location.ilike('%????%')
).count()

output = {
    "category_ids": cat_ids,
    "ads_count_with_location_irbid": count_raw,
}

with open('test_241.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

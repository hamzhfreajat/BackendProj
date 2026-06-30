import sys
import json
from database import SessionLocal
from sqlalchemy import text
import models

db = SessionLocal()

loc_query = "اربد"

sql = "SELECT DISTINCT location FROM ads WHERE is_published = True AND location ILIKE :loc LIMIT 10"
locs = db.execute(text(sql), {"loc": f"%{loc_query}%"}).fetchall()

output = {
    "ar": [l[0] for l in locs],
}

with open('test_locations.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

import sys
sys.path.append('d:\\open\\classifieds-app\\backend')

from database import SessionLocal
from sqlalchemy import text
import json

db = SessionLocal()

query = "شقه للايجار في عمان"
sql = """
    SELECT ad_id, deal_type, property_type, search_text
    FROM ad_search_index
    WHERE deal_type = 'RENT' 
      AND property_type = 'APARTMENT'
      AND search_text ILIKE '%عمان%'
    LIMIT 5
"""

res = db.execute(text(sql)).fetchall()
out = []
for r in res:
    out.append({"ad_id": r.ad_id, "deal_type": r.deal_type, "property_type": r.property_type, "search_text": r.search_text})

with open('debug_search_out2.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

db.close()

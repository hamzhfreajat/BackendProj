import sys
import json
from database import SessionLocal
from search_service import SearchService
from sqlalchemy import text

db = SessionLocal()

query_text = "شقق للايجار في اربد"
ranked_ad_ids = SearchService.search_properties(db, query_text, limit=1000)

sql = "SELECT DISTINCT location FROM ads WHERE id IN :ids"
locs = db.execute(text(sql), {"ids": tuple(ranked_ad_ids) if ranked_ad_ids else (-1,)}).fetchall()

with open('test_276_locs.json', 'w', encoding='utf-8') as f:
    json.dump([l[0] for l in locs], f, ensure_ascii=False, indent=2)

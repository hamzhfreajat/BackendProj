import sys
sys.path.append('d:\\open\\classifieds-app\\backend')

from database import SessionLocal
from search_service import SearchService
from search_parser import QueryParserService

db = SessionLocal()

query = "شقة مفروشة لقطة للبيع طابو في خلدا"
import json

parsed = QueryParserService.parse(query)
results = SearchService.search_properties(raw_query=query, db=db, limit=10)
from sqlalchemy import text
count = db.execute(text("SELECT COUNT(*) FROM ad_search_index")).scalar()

out = {
    "query": query,
    "parsed": parsed.model_dump() if parsed else None,
    "results": results,
    "total_rows": count
}

with open('debug_search_out.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

db.close()

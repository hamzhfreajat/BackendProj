import sys
import json
from database import SessionLocal
from search_service import SearchService

db = SessionLocal()

query_text = "شقق للبيع بالجاردنز"
ranked_ad_ids = SearchService.search_properties(db, query_text, limit=1000)

output = {
    "num_results": len(ranked_ad_ids)
}

with open('test_search_jordan.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

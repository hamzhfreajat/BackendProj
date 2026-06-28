import sys
import json
from database import SessionLocal
from search_service import SearchService
import search_parser

db = SessionLocal()

query = "شقق للايجار في اربد"
parsed = search_parser.QueryParserService.parse(query)

# Raw match using search_properties
ranked_ad_ids = SearchService.search_properties(db, query, limit=1000)

output = {
    "query": query,
    "parsed": {
        "deal_type": parsed.deal_type,
        "property_type": parsed.property_type,
        "location": parsed.location,
    },
    "num_results": len(ranked_ad_ids),
    "ad_ids": ranked_ad_ids[:20]
}

with open('test_search_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

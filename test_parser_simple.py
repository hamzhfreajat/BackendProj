import sys
import json
sys.path.append('d:\\open\\classifieds-app\\backend')
from search_parser import QueryParserService
from search_service import SearchService
from database import SessionLocal

db = SessionLocal()

q = "شقق للايجار بالجاردنز"
try:
    parsed = QueryParserService.parse(q)
    count = SearchService.count_properties(db, q)
    with open('test_out.json', 'w', encoding='utf-8') as f:
        json.dump({"parsed": getattr(parsed, 'model_dump', parsed.dict)(), "count": count}, f, ensure_ascii=False)
except Exception as e:
    with open('test_out.json', 'w', encoding='utf-8') as f:
        f.write(str(e))

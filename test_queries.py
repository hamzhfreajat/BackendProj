import sys
import json
from search_parser import QueryParserService

queries = [
    "شقق للايجار في اربد",
    "اراضي للبيع بالمفرق"
]

output = []
for q in queries:
    parsed = QueryParserService.parse(q)
    output.append({
        "query": q,
        "deal_type": parsed.deal_type,
        "property_type": parsed.property_type,
        "location": parsed.location
    })

with open('test_queries.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

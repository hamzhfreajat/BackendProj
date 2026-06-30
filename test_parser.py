import sys
import json
from search_parser import QueryParserService

query = "شقق للبيع بالجاردنز"
parsed = QueryParserService.parse(query)

output = {
    "deal_type": parsed.deal_type,
    "property_type": parsed.property_type,
    "location": parsed.location,
    "features": parsed.features,
}

with open('test_parser.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

import sys
import json
from database import SessionLocal
from autocomplete_service import AutocompleteService

queries = [
    "شقق للايجار في اربد",
    "اراضي للبيع بالمفرق",
    "مكاتب للبيع في عمان",
    "عمارة للايجار",
    "مزارع للبيع"
]

db = SessionLocal()
output = []
for q in queries:
    res = AutocompleteService.generate_suggestions(db, q)
    output.append({
        "query": q,
        "intent": res.get("intent", {})
    })

with open('test_cat_routing.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

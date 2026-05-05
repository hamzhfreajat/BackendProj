import sys
sys.path.append('d:\\open\\classifieds-app\\backend')

from database import SessionLocal
from autocomplete_service import AutocompleteService
import json

db = SessionLocal()

queries = [
    "شقة في خلدا",
    "بيت للبيع بالتقسيط",
    "شقة أقل من 50 ألف"
]

results = []
for q in queries:
    res = AutocompleteService.generate_suggestions(db, q)
    results.append({"QUERY": q, "RESULT": res})

with open('test_autocomplete_output.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

db.close()


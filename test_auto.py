import sys
sys.path.append('d:\\open\\classifieds-app\\backend')
from autocomplete_service import AutocompleteService
from database import SessionLocal

db = SessionLocal()
q = "شقق للايجار بالجاردنز"
try:
    res = AutocompleteService.generate_suggestions(db, q)
    import json
    with open('test_auto.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False)
except Exception as e:
    with open('test_auto.json', 'w', encoding='utf-8') as f:
        f.write(str(e))

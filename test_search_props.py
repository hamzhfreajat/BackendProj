import sys
sys.path.append('d:\\open\\classifieds-app\\backend')
from search_service import SearchService
from database import SessionLocal

db = SessionLocal()
q = "شقق للايجار بالجاردنز"
try:
    results = SearchService.search_properties(db, q, limit=5)
    print("Results length:", len(results))
    if len(results) > 0:
        print("First result ID:", results[0].id)
except Exception as e:
    print("Error:", e)

from database import SessionLocal
from models import Ad
from search_service import SearchService

db = SessionLocal()
# Get a single ad to test
ad = db.query(Ad).filter(Ad.is_published == True).first()
if ad:
    try:
        SearchService.sync_ad_to_search_index(db, ad, commit=True)
        print("Successfully synced one ad.")
    except Exception as e:
        print(f"Error syncing ad: {e}")
else:
    print("No ads found.")

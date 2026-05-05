from database import SessionLocal
import models
from search_service import SearchService
from sqlalchemy.orm import joinedload

def backfill():
    db = SessionLocal()
    try:
        ads = db.query(models.Ad).options(
            joinedload(models.Ad.category),
            joinedload(models.Ad.real_estate_detail),
            joinedload(models.Ad.linked_tags)
        ).all()
        total = len(ads)
        print(f"Starting backfill for {total} ads...")
        
        for i, ad in enumerate(ads):
            SearchService.sync_ad_to_search_index(db, ad, commit=True)
            if i % 100 == 0:
                print(f"Synced {i}/{total} ads...")
                
        print("✅ Backfill complete.")
    except Exception as e:
        print(f"❌ Error during backfill: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()

import psycopg2
from search_service import SearchService
import models
from database import SessionLocal

def fix_ads():
    # Fetch IDs first
    db = SessionLocal()
    try:
        ads = db.query(models.Ad.id).filter(models.Ad.attributes.isnot(None)).all()
        ad_ids = [ad.id for ad in ads]
    finally:
        db.close()
        
    fixed_count = 0
    
    for ad_id in ad_ids:
        db = SessionLocal()
        try:
            ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
            if not ad:
                continue
                
            attr = ad.attributes or {}
            city = attr.get('city')
            region = attr.get('region')
            
            if city and region:
                correct_loc = f"{city}, {region}"
                if ad.location != correct_loc:
                    print(f"Fixing ad {ad.id}")
                    ad.location = correct_loc
                    SearchService.sync_ad_to_search_index(db, ad)
                    db.commit()
                    fixed_count += 1
        except Exception as e:
            print(f"Error on ad {ad_id}: {e}")
            db.rollback()
        finally:
            db.close()
            
    print(f"Fixed {fixed_count} ads and synced them to search index!")

if __name__ == "__main__":
    fix_ads()

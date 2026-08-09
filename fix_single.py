from search_service import SearchService
import models
from database import SessionLocal

db = SessionLocal()
try:
    ad = db.query(models.Ad).filter(models.Ad.id == 25989).first()
    if ad:
        correct_loc = "إربد, حكما"
        ad.location = correct_loc
        SearchService.sync_ad_to_search_index(db, ad)
        db.commit()
        print('Ad 25989 fixed instantly!')
except Exception as e:
    print('Error:', e)
finally:
    db.close()

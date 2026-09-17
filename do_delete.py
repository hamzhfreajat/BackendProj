from database import SessionLocal
from sqlalchemy import text
from models import AdRealEstateDetail, AdSearchIndex, SavedAd, AdReport, AdClickTracking, Ad

db = SessionLocal()

ad_id = 28087
db.query(AdRealEstateDetail).filter(AdRealEstateDetail.ad_id == ad_id).delete()
db.query(AdSearchIndex).filter(AdSearchIndex.ad_id == ad_id).delete()
db.query(SavedAd).filter(SavedAd.ad_id == ad_id).delete()
db.query(AdReport).filter(AdReport.ad_id == ad_id).delete()
db.query(AdClickTracking).filter(AdClickTracking.ad_id == ad_id).delete()

db_ad = db.query(Ad).filter(Ad.id == ad_id).first()
if db_ad:
    db.delete(db_ad)
    db.commit()
    print("Deleted successfully!")
else:
    print("Ad not found!")

db.close()

from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
sql = "SELECT count(*) FROM ad_search_index"
res3 = db.execute(text(sql)).scalar()
print('Search Index Ads:', res3)

import sys
sys.path.append('d:\\open\\classifieds-app\\backend')
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
affordable = db.execute(text("SELECT COUNT(1) FROM ad_search_index WHERE search_text ILIKE '%affordable%'")).scalar()
hot_deal = db.execute(text("SELECT COUNT(1) FROM ad_search_index WHERE search_text ILIKE '%hot_deal%'")).scalar()
balcony = db.execute(text("SELECT COUNT(1) FROM ad_search_index WHERE search_text ILIKE '%balcony%'")).scalar()

print(f"Affordable: {affordable}")
print(f"Hot deal: {hot_deal}")
print(f"Balcony: {balcony}")

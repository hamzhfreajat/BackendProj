import sys
sys.path.append('d:\\open\\classifieds-app\\backend')
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
khalda_ads = db.execute(text("SELECT ad_id, title, search_text FROM ad_search_index WHERE search_text ILIKE '%خلدا%'")).fetchall()
print(f"Total ads in Khalda: {len(khalda_ads)}")
for ad in khalda_ads[:5]:
    print(ad.title)

tla_ali = db.execute(text("SELECT COUNT(1) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%'")).scalar()
print(f"Total ads in Tlaa Al Ali: {tla_ali}")

zarka = db.execute(text("SELECT COUNT(1) FROM ad_search_index WHERE search_text ILIKE '%الزرقاء%'")).scalar()
print(f"Total ads in Zarka: {zarka}")


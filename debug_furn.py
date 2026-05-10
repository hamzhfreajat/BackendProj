import sys
import io
sys.path.append('.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from database import SessionLocal
from sqlalchemy import text
import models
from search_parser import QueryParserService

db = SessionLocal()
ad_id = db.execute(text("SELECT ad_id FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%' AND property_type = 'APARTMENT' AND deal_type = 'RENT' AND search_text ILIKE '%مفروش%' LIMIT 1")).scalar()
print('Ad ID:', ad_id)
if ad_id:
    ad = db.query(models.Ad).get(ad_id)
    print('Title:', ad.title)
    print('Desc:', ad.description)
    print('DB furnished:', ad.real_estate_detail.furnished if ad.real_estate_detail else 'No detail')
    parsed = QueryParserService.parse(f"{ad.title} {ad.description} {ad.location}")
    print('Parsed furnished:', parsed.furnished)
db.close()

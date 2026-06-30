import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

output = {}

output['Total published ads'] = db.execute(text("SELECT count(*) FROM ads WHERE is_published = True")).scalar()

output['Raw ads with location اربد'] = db.execute(text("SELECT count(*) FROM ads WHERE is_published = True AND location ILIKE '%اربد%'")).scalar()

output['Indexed ads with property_type APARTMENT, deal_type RENT, location اربد'] = db.execute(text("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%اربد%' AND property_type='APARTMENT' AND deal_type='RENT'")).scalar()

output['Total Indexed ads in اربد'] = db.execute(text("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%اربد%'")).scalar()

output['Total Indexed APARTMENT RENT'] = db.execute(text("SELECT count(*) FROM ad_search_index WHERE property_type='APARTMENT' AND deal_type='RENT'")).scalar()

with open('test_counts_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

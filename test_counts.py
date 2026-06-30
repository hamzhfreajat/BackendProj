import sys
import os
sys.path.append(r"D:\open\classifieds-app\backend")
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

# Check count in ads table
sql_ads = """
SELECT COUNT(*) FROM ads 
WHERE category_id IN (SELECT id FROM categories WHERE name_ar LIKE '%???%')
AND deal_type = 'RENT'
AND location LIKE '%????%'
"""
count_ads = db.execute(text(sql_ads)).scalar()

# Check count in ad_search_index
sql_index = """
SELECT COUNT(*) FROM ad_search_index
WHERE property_type = 'APARTMENT'
AND deal_type = 'RENT'
AND search_text ILIKE '%????%'
"""
count_index = db.execute(text(sql_index)).scalar()

print(f"Ads count: {count_ads}")
print(f"Index count: {count_index}")

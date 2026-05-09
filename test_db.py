import sys
import io
sys.path.append('.')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()

def run(q):
    return db.execute(text(q)).scalar()

print('Total:', run('SELECT count(*) FROM ad_search_index'))
print('Tlaa:', run("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%'"))
print('Apartment:', run("SELECT count(*) FROM ad_search_index WHERE property_type = 'APARTMENT'"))
print('Rent:', run("SELECT count(*) FROM ad_search_index WHERE deal_type = 'RENT'"))
print('Furnished:', run("SELECT count(*) FROM ad_search_index WHERE furnished = true"))

# Intersections
print('Tlaa + Apt + Rent:', run("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%' AND property_type = 'APARTMENT' AND deal_type = 'RENT'"))
print('Tlaa + Apt + Rent + Furnished:', run("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%' AND property_type = 'APARTMENT' AND deal_type = 'RENT' AND furnished = true"))

# What if furnished is null?
print('Tlaa + Apt + Rent + Furnished IS NULL:', run("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%' AND property_type = 'APARTMENT' AND deal_type = 'RENT' AND furnished IS NULL"))
print('Tlaa + Apt + Rent + Furnished IS FALSE:', run("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%' AND property_type = 'APARTMENT' AND deal_type = 'RENT' AND furnished = false"))

# Features JSON
print('Features jsonb check:', run("SELECT count(*) FROM ad_search_index WHERE search_text ILIKE '%تلاع العلي%' AND property_type = 'APARTMENT' AND deal_type = 'RENT' AND search_text ILIKE '%مفروش%'"))

db.close()

import sys
import json
from database import SessionLocal
from search_service import SearchService
import search_parser
import models

db = SessionLocal()

query_text = "شقق للايجار في اربد"
ranked_ad_ids = SearchService.search_properties(db, query_text, limit=1000)

query = db.query(models.Ad).filter(models.Ad.is_published == True)
if ranked_ad_ids:
    query = query.filter(models.Ad.id.in_(ranked_ad_ids))

ads = query.all()

# Count by category
categories = {}
for ad in ads:
    cat = ad.category.name_ar if ad.category and hasattr(ad.category, 'name_ar') else (ad.category.name if ad.category else "None")
    categories[cat] = categories.get(cat, 0) + 1

# Check with location filter "اربد"
query_loc = db.query(models.Ad).filter(models.Ad.is_published == True)
if ranked_ad_ids:
    query_loc = query_loc.filter(models.Ad.id.in_(ranked_ad_ids))
query_loc = query_loc.filter(models.Ad.location.ilike('%اربد%'))
ads_loc = query_loc.count()

output = {
    "total_matched": len(ads),
    "by_category": categories,
    "matched_with_strict_location": ads_loc
}

with open('test_filters.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

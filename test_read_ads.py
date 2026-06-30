import sys
import json
from database import SessionLocal
from search_service import SearchService
import search_parser
import models
from sqlalchemy.sql.expression import case

db = SessionLocal()

query_text = "شقق للايجار في اربد"
ranked_ad_ids = SearchService.search_properties(db, query_text, limit=1000)

query = db.query(models.Ad)
query = query.filter(models.Ad.is_published == True) # usually frontend only requests published or we assume published
if ranked_ad_ids:
    query = query.filter(models.Ad.id.in_(ranked_ad_ids))

ads = query.all()

output = {
    "num_results_from_search_index": len(ranked_ad_ids),
    "num_results_from_ads_table": len(ads),
}

with open('test_read_ads_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

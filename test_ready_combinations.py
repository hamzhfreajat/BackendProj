import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models
from sqlalchemy import func

db = SessionLocal()

parent_ids = db.query(models.Category.parent_id).filter(models.Category.parent_id.isnot(None)).distinct()
leaf_categories = db.query(models.Category).filter(~models.Category.id.in_(parent_ids)).all()
leaf_cat_ids = [c.id for c in leaf_categories]
leaf_cat_map = {c.id: c.name for c in leaf_categories}

results = db.query(
    models.AdSearchIndex.region_id,
    models.AdSearchIndex.category_id,
    func.count(models.AdSearchIndex.ad_id).label('post_count')
).filter(
    models.AdSearchIndex.category_id.in_(leaf_cat_ids)
).group_by(
    models.AdSearchIndex.region_id,
    models.AdSearchIndex.category_id
).having(
    func.count(models.AdSearchIndex.ad_id) >= 50
).all()

region_ids = [r.region_id for r in results]
regions = db.query(models.Region).filter(models.Region.id.in_(region_ids)).all()
region_map = {r.id: r.name_ar for r in regions}

output = []
for r in results:
    region_name = region_map.get(r.region_id, "Unknown")
    cat_name = leaf_cat_map.get(r.category_id, "Unknown")
    output.append({
        "region_name": region_name,
        "category_name": cat_name,
        "count": r.post_count
    })

print(output)

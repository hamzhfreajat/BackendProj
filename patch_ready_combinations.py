import sys

with open("fb_publisher_router.py", "r", encoding="utf-8") as f:
    content = f.read()

new_endpoint = """
@router.get("/ready-combinations")
def get_ready_combinations(db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    # Find leaf categories
    parent_ids = db.query(models.Category.parent_id).filter(models.Category.parent_id.isnot(None)).distinct()
    leaf_categories = db.query(models.Category).filter(~models.Category.id.in_(parent_ids)).all()
    leaf_cat_ids = [c.id for c in leaf_categories]
    leaf_cat_map = {c.id: c.name for c in leaf_categories}
    
    # Group ads in AdSearchIndex by region_id and category_id
    results = db.query(
        models.AdSearchIndex.region_id,
        models.AdSearchIndex.category_id,
        func.count(models.AdSearchIndex.ad_id).label('post_count')
    ).filter(
        models.AdSearchIndex.category_id.in_(leaf_cat_ids),
        models.AdSearchIndex.region_id.isnot(None)
    ).group_by(
        models.AdSearchIndex.region_id,
        models.AdSearchIndex.category_id
    ).having(
        func.count(models.AdSearchIndex.ad_id) >= 50
    ).all()
    
    region_ids = [r.region_id for r in results if r.region_id]
    regions = db.query(models.Region).filter(models.Region.id.in_(region_ids)).all()
    region_map = {r.id: r.name_ar for r in regions}
    
    output = []
    for r in results:
        if not r.region_id:
            continue
        region_name = region_map.get(r.region_id)
        if not region_name:
            continue
            
        cat_name = leaf_cat_map.get(r.category_id, "Unknown")
        
        output.append({
            "region_name": region_name,
            "category_name": cat_name,
            "category_id": r.category_id,
            "count": min(r.post_count, 20),
            "actual_count": r.post_count
        })
        
    return output
"""

if "@router.get(\"/ready-combinations\")" not in content:
    content += new_endpoint
    with open("fb_publisher_router.py", "w", encoding="utf-8") as f:
        f.write(content)

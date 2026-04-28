import os
import json
from database import SessionLocal
from models import Ad, City, Region
from sqlalchemy import or_

def check_locations():
    db = SessionLocal()
    
    query = db.query(Ad.location).filter(
        or_(
            Ad.location.ilike('%other%'),
            Ad.location.ilike('%أخرى%'),
            Ad.location.ilike('%اخرى%'),
            Ad.location.ilike('%غير محدد%')
        )
    ).distinct()
    
    locations = [r[0] for r in query.all()]
    
    results = {"distinct_locations": locations, "counts": {}, "total_ads": 0}
    for loc in locations:
        count = db.query(Ad).filter(Ad.location == loc).count()
        results["counts"][loc] = count
        results["total_ads"] += count
        
    with open("location_counts.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    db.close()

if __name__ == "__main__":
    check_locations()

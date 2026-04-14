from database import SessionLocal
import models
from sqlalchemy import func

def test():
    db = SessionLocal()
    # 1. Total logs
    logs = db.query(models.UserActivityLog).count()
    print(f"Total Logs: {logs}")
    
    # 2. Top Category Global
    top_global = db.query(models.UserActivityLog.category_id, func.count(models.UserActivityLog.id).label('c'))\
            .filter(models.UserActivityLog.category_id.isnot(None))\
            .group_by(models.UserActivityLog.category_id)\
            .order_by(func.count(models.UserActivityLog.id).desc())\
            .first()
            
    print(f"Top global cat_id: {top_global}")
    
    # Check Ads for that category
    if top_global:
        cid = top_global[0]
        ads_count = db.query(models.Ad).filter(models.Ad.category_id == cid).count()
        print(f"Ads for cat {cid}: {ads_count}")

import sys
test()

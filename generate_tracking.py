from database import SessionLocal
import models
import random
from datetime import datetime, timedelta

def run():
    db = SessionLocal()
    
    # 1. Fetch some real categories
    cats = db.query(models.Category).limit(10).all()
    if not cats:
        return
        
    print("Generating tracking data...")
    actions = ["VIEW_CATEGORY", "APPLY_FILTER", "SEARCH_QUERY", "VIEW_AD"]
    
    for _ in range(50):
        c = random.choice(cats)
        act = random.choice(actions)
        
        filters = None
        if act == "APPLY_FILTER":
            filters = {"min_price": random.randint(100, 5000), "max_price": random.randint(5000, 20000)}
            if random.choice([True, False]):
                filters["tags"] = ["مفروشة"]
                
        log = models.UserActivityLog(
            action_type=act,
            category_id=c.id,
            filters_json=filters,
        )
        db.add(log)
        
    db.commit()
    print("Done generating tracking data.")

if __name__ == "__main__":
    run()

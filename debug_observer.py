import asyncio
from database import SessionLocal
import models
from observer import trigger_saved_filter_notifications

def test_observer():
    db = SessionLocal()
    
    # 1. Check all saved filters
    filters = db.query(models.SavedFilter).all()
    print(f"Total filters in DB: {len(filters)}")
    for f in filters:
        try:
            print(f"Filter ID: {f.id}, Cat: {f.category_id}, Alert: {f.alert_frequency}, MinP: {f.min_price}, Tags: {f.tags}")
        except UnicodeEncodeError:
            print(f"Filter ID: {f.id}, Cat: {f.category_id}, MinP: {f.min_price}, Tags: {f.tags} (alert frequency contains arabic)")
            
    # 2. Find the latest ad inserted
    ad = db.query(models.Ad).order_by(models.Ad.id.desc()).first()
    if not ad:
        print("No ads found.")
        return
        
    print(f"\nEvaluating Ad ID: {ad.id}, Category: {ad.category_id}, Price: {ad.price}, Tags: {[t.name for t in ad.linked_tags]}")
    
    # 3. Simulate the exact query
    matched_filters = db.query(models.SavedFilter).filter(
        models.SavedFilter.is_active == True,
        models.SavedFilter.alert_frequency.in_(['فوري', 'instant']),
        (models.SavedFilter.category_id.is_(None) | (models.SavedFilter.category_id == ad.category_id))
    ).all()
    
    print(f"\nSQL Pre-filtered Matches: {len(matched_filters)}")
    
    # 4. Trigger the actual observer
    print("\nRunning trigger_saved_filter_notifications...")
    trigger_saved_filter_notifications(db, ad)
    print("Done running trigger.")

if __name__ == "__main__":
    test_observer()

import os
from database import SessionLocal
from models import Ad, AdSearchIndex, Category, SavedGroup, SavedFilter, UserActivityLog, User

db = SessionLocal()
try:
    # 1. Move Ads
    ads = db.query(Ad).filter(Ad.category_id == 3023).all()
    print(f"Found {len(ads)} ads with category_id 3023")
    for ad in ads:
        ad.category_id = 302
        # If there is leaf_category_name in attributes, update it
        if ad.attributes and isinstance(ad.attributes, dict):
            if 'leaf_category_name' in ad.attributes:
                ad.attributes['leaf_category_name'] = 'ستوديوهات للإيجار'
            db.add(ad)
    
    # 2. Update AdSearchIndex
    search_indices = db.query(AdSearchIndex).filter(AdSearchIndex.category_id == 3023).all()
    print(f"Found {len(search_indices)} search indices with category_id 3023")
    for si in search_indices:
        si.category_id = 302
        db.add(si)

    # 3. Update any other tables referencing category_id
    saved_groups = db.query(SavedGroup).filter(SavedGroup.category_id == 3023).all()
    for sg in saved_groups:
        sg.category_id = 302
        db.add(sg)
        
    saved_filters = db.query(SavedFilter).filter(SavedFilter.category_id == 3023).all()
    for sf in saved_filters:
        sf.category_id = 302
        db.add(sf)
        
    user_activities = db.query(UserActivityLog).filter(UserActivityLog.category_id == 3023).all()
    for ua in user_activities:
        ua.category_id = 302
        db.add(ua)

    users_latest_cat = db.query(User).filter(User.latest_category_id == 3023).all()
    for user in users_latest_cat:
        user.latest_category_id = 302
        db.add(user)

    # 4. Delete the category
    cat_to_delete = db.query(Category).filter(Category.id == 3023).first()
    if cat_to_delete:
        db.delete(cat_to_delete)
        print("Deleted category 3023")
    else:
        print("Category 3023 not found")

    db.commit()
    print("Database update successful!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()

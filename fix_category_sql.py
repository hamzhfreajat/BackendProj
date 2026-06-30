import os
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 1. Update Ads
    db.execute(text("UPDATE ads SET category_id = 302 WHERE category_id = 3023;"))
    db.execute(text("UPDATE ads SET attributes = jsonb_set(attributes, '{leaf_category_name}', '\"ستوديوهات للإيجار\"'::jsonb) WHERE category_id = 302 AND attributes->>'leaf_category_name' = 'ستوديو فندقي / مخدوم';"))
    
    # 2. Update AdSearchIndex
    db.execute(text("UPDATE ad_search_index SET category_id = 302 WHERE category_id = 3023;"))

    # 3. Update any other tables referencing category_id
    db.execute(text("UPDATE saved_groups SET category_id = 302 WHERE category_id = 3023;"))
    db.execute(text("UPDATE saved_filters SET category_id = 302 WHERE category_id = 3023;"))
    db.execute(text("UPDATE user_activity_logs SET category_id = 302 WHERE category_id = 3023;"))
    db.execute(text("UPDATE users SET latest_category_id = 302 WHERE latest_category_id = 3023;"))

    # 4. Delete the category
    db.execute(text("DELETE FROM categories WHERE id = 3023;"))

    db.commit()
    print("Database update successful!")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()

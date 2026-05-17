import asyncio
from database import SessionLocal
from models import Category, Ad, AdSearchIndex
from sqlalchemy import select, update, delete

async def main():
    db = SessionLocal()
    
    # The ID of the category to remove
    old_cat_id = 10015
    # The ID of the target category
    target_cat_id = 10301
    
    old_cat = db.query(Category).filter(Category.id == old_cat_id).first()
    target_cat = db.query(Category).filter(Category.id == target_cat_id).first()
    
    if old_cat and target_cat:
        print(f"Moving from {old_cat.id} to {target_cat.id}")
        
        # 1. Update Ads
        ads_updated = db.execute(
            update(Ad).where(Ad.category_id == old_cat.id).values(category_id=target_cat.id)
        )
        print("Ads updated:", ads_updated.rowcount)
        
        # 2. Update AdSearchIndex
        index_updated = db.execute(
            update(AdSearchIndex).where(AdSearchIndex.category_id == old_cat.id).values(category_id=target_cat.id)
        )
        print("Search Index updated:", index_updated.rowcount)
        
        # 3. Delete Category
        db.execute(delete(Category).where(Category.id == old_cat.id))
        print("Old category deleted.")
        
        db.commit()
    else:
        print("Not found:")
        print("old_cat found:", old_cat is not None)
        print("target_cat found:", target_cat is not None)
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())

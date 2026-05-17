import asyncio
from database import SessionLocal
from models import Category, Ad, AdSearchIndex
from sqlalchemy import select, update, delete

async def main():
    db = SessionLocal()
    
    # Find شقق فندقية مخدومة
    cats = db.query(Category).filter(Category.name.like('%شقق فندقية%')).all()
    old_cat = cats[0] if cats else None
    
    # Find شقق للبيع
    cats_sale = db.query(Category).filter(Category.name.like('%شقق للبيع%')).all()
    target_cat = cats_sale[0] if cats_sale else None
    
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
        if target_cat is None:
            c = db.query(Category).filter(Category.id == 10101).first()
            print("Is 10101 apartments for sale? ", c.id if c else "no")
            c = db.query(Category).filter(Category.id == 201).first()
            print("Is 201 apartments for sale? ", c.id if c else "no")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Category, Ad
from sqlalchemy.orm import Session

# List of keywords that exist in Ad Details form and shouldn't be categories
# Rooms: ستوديو, 1, 2, 3... 
# Rent duration: يومي, شهري, سنوي, أسبوعي
# Floor: تسوية, طابق, أرضي, رووف, بنتهاوس
# Others: مفروش (already done), فارغ (already done)

KEYWORDS = [
    # Rent duration concepts
    "يومي", "شهري", "سنوي", "أسبوعي", "سياحي",
    # Room counts
     "3 غرف", "غرفة وصالة",
    # Floor types
    "طابقية", "أرضية", "دوبلكس", "رووف", "بنتهاوس", "طابق أخير", "طابقين", "تسوية"
]

def run_migration():
    db: Session = SessionLocal()
    try:
        # Find all categories matching any of the keywords
        target_cats = set()
        for c in db.query(Category).all():
            for kw in KEYWORDS:
                if kw in c.name and c.parent_id is not None:
                    # Ignore root top level categories just in case
                    target_cats.add(c)

        print(f"Found {len(target_cats)} redundant granular categories.")

        # Save to JSON for visibility tracking
        res = [{'id': c.id, 'name': c.name, 'parent_id': c.parent_id} for c in target_cats]
        with open('temp_redundants.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False))

        # Perform the safe upward migration 
        for c in target_cats:
            parent_id = c.parent_id
            
            # 1. Reassign ads
            ads_to_move = db.query(Ad).filter(Ad.category_id == c.id).all()
            for ad in ads_to_move:
                ad.category_id = parent_id

            # 2. Reassign subcategories of THIS category to the parent category
            subcats = db.query(Category).filter(Category.parent_id == c.id).all()
            for sub in subcats:
                sub.parent_id = parent_id

            # 3. Delete the category itself
            # Have to fetch the fresh instance because it might be altered in SQLAlchemy session loop
            current_c = db.query(Category).filter(Category.id == c.id).first()
            if current_c:
                db.delete(current_c)

        db.commit()
        print("\nSuccessfully rempapped and deleted all granular subcategories.")

    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()

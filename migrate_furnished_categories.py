import os
import sys

# Add current dir to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Category, Ad
from sqlalchemy.orm import Session

def run_migration():
    db: Session = SessionLocal()
    try:
        # Find all categories that act as 'Furnished' or 'Unfurnished'
        target_cats = []
        for c in db.query(Category).all():
            if 'مفروش' in c.name or 'فارغ' in c.name:
                target_cats.append(c)

        print(f"Found {len(target_cats)} redundant furnished/unfurnished categories.")

        for c in target_cats:
            parent_id = c.parent_id
            
            # If a top-level category somehow has this name, we skip to avoid breaking the root.
            if not parent_id:
                print(f"Skipping {c.id} - It has no parent.")
                continue

            print(f"\nProcessing [{c.id}] -> Parent is [{parent_id}]")

            # 1. Reassign ads directly in this category to the parent category
            ads_to_move = db.query(Ad).filter(Ad.category_id == c.id).all()
            for ad in ads_to_move:
                ad.category_id = parent_id
            print(f"  Moved {len(ads_to_move)} ads to parent [{parent_id}].")

            # 2. Reassign subcategories of THIS category to the parent category
            subcats = db.query(Category).filter(Category.parent_id == c.id).all()
            for sub in subcats:
                sub.parent_id = parent_id
                print(f"  Reparented subcategory [{sub.id}] to [{parent_id}].")

            # 3. Delete the category itself
            db.delete(c)
            print(f"  Deleted category [{c.id}].")

        db.commit()
        print("\nSuccessfully rempapped and deleted all furnished subcategories.")

    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()

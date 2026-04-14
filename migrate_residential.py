import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Category
from sqlalchemy.orm import Session

def run_migration():
    db: Session = SessionLocal()
    try:
        # ID 310 is "سكني"
        new_cats = [
            (3101, "فلل وقصور", None, None, None),
            (3102, "بيوت مستقلة للإيجار", None, None, None),
            (3103, "دوبلكس / بنتهاوس", None, None, None),
            (3104, "طابق كامل للإيجار", None, None, None),
            (3105, "ملحق / روف", None, None, None),
            (3999, "أخرى", None, None, None),
        ]
        
        for cat_id, name, desc, icon, color in new_cats:
            existing = db.query(Category).filter(Category.id == cat_id).first()
            if not existing:
                new_cat = Category(
                    id=cat_id,
                    parent_id=310,
                    name=name,
                    description=desc,
                    icon_name=icon,
                    color_hex=color
                )
                db.add(new_cat)
        
        db.commit()

    except Exception as e:
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()

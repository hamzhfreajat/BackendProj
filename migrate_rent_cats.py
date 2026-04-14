import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Category, Ad
from sqlalchemy.orm import Session

def run_migration():
    db: Session = SessionLocal()
    try:
        # Define New Categories under Rent (ID: 3)
        new_cats = [
            (310, "سكني", "شقق، فلل، منازل واستديوهات", "home", "#4CAF50"),
            (311, "تجاري", "مكاتب، معارض ومخازن", "store", "#FF9800"),
            (313, "أراضي", "أراضي للإيجار والاستثمار", "landscape", "#8BC34A"),
            (314, "مزارع", "مزارع للإيجار", "agriculture", "#4CAF50"),
            (315, "شاليهات / منتجعات", "شاليهات ومنتجعات للإيجار", "pool", "#00BCD4"),
            (316, "بيوت ريفية", "بيوت ريفية وتراثية", "cottage", "#8D6E63")
        ]
        
        # Insert New Categories
        for cat_id, name, desc, icon, color in new_cats:
            existing = db.query(Category).filter(Category.id == cat_id).first()
            if not existing:
                new_cat = Category(
                    id=cat_id,
                    parent_id=3,
                    name=name,
                    description=desc,
                    icon_name=icon,
                    color_hex=color
                )
                db.add(new_cat)
        
        db.flush() # ensure they are in the session

        # 1. Remap Residential (301, 302) -> 310
        for residential_id in [301, 302]:
            c = db.query(Category).filter(Category.id == residential_id).first()
            if c:
                c.parent_id = 310

        # 2. Remap Commercial (303, 304) -> 311
        for commercial_id in [303, 304]:
            c = db.query(Category).filter(Category.id == commercial_id).first()
            if c:
                c.parent_id = 311

        # 3. Rename Shared Housing (306) -> "سكن مشترك" under 3
        c306 = db.query(Category).filter(Category.id == 306).first()
        if c306:
            c306.name = "سكن مشترك"
            c306.parent_id = 3

        db.commit()

    except Exception as e:
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()

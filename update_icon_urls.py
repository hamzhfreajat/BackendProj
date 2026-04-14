import os
import sys
import codecs

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from database import SessionLocal
from models import Category

# Map category IDs to the icon filenames we generated
ICON_MAP = {
    1: "real_estate.png",    # عقارات للبيع
    2: "rental.png",         # عقارات للإيجار
    3: "vehicles.png",       # سيارات ومركبات
    4: "services.png",       # خدمات
    5: "electronics.png",    # إلكترونيات
    6: "furniture.png",      # أثاث ومفروشات
    7: "fashion.png",        # أزياء وملابس
    8: "kids.png",           # أطفال ورضع
    9: "pets.png",           # حيوانات أليفة
    10: "jobs.png",          # وظائف
    11: "education.png",     # تعليم
    12: "sports.png",        # رياضة
    13: "food.png",          # طعام ومطاعم
}

def main():
    db = SessionLocal()
    updated = 0
    
    for cat_id, icon_file in ICON_MAP.items():
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if cat:
            cat.icon_name = f"/static/icons/{icon_file}"
            updated += 1
    
    db.commit()
    print(f"Updated {updated} main categories with local icon paths.")
    db.close()

if __name__ == "__main__":
    main()

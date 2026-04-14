import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Category
import codecs

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def delete_children(db, parent_id):
    children = db.query(Category).filter(Category.parent_id == parent_id).all()
    for child in children:
        delete_children(db, child.id)
        db.delete(child)

def add_categories(db, parent_id, items, parent_icon, parent_color):
    total_added = 0
    if isinstance(items, list):
        for name in items:
            new_cat = Category(
                name=name,
                parent_id=parent_id,
                icon_name=parent_icon,
                color_hex=parent_color
            )
            db.add(new_cat)
            db.flush()
            total_added += 1
    elif isinstance(items, dict):
        for name, sub_items in items.items():
            new_cat = Category(
                name=name,
                parent_id=parent_id,
                icon_name=parent_icon,
                color_hex=parent_color
            )
            db.add(new_cat)
            db.flush()
            cat_id = new_cat.id
            total_added += 1
            total_added += add_categories(db, cat_id, sub_items, parent_icon, parent_color)
    return total_added

def main():
    db = SessionLocal()
    parent_id = 105
    parent_category = db.query(Category).filter(Category.id == parent_id).first()
    
    if not parent_category:
        print(f"Parent {parent_id} not found")
        db.close()
        return

    # Delete existing children
    delete_children(db, parent_id)
    db.commit()
    print("Deleted old children for 105.")

    data = {
        "باصات": [
            "باصات ركاب", "باصات صغيرة", "باصات نقل عام", "باصات مدرسية", "باصات سياحية",
            "ميكروباص / فان", "باصات VIP", "باصات كهربائية", "باصات ديزل", "باصات جديدة", 
            "باصات مستعملة", "قطع غيار باصات", "أخرى"
        ],
        "شاحنات": [
            "صندوق", "تنك", "براد", "راس تريلا", "ونش", "شاسيه", "قلاب", "سطحة", "نقل سيارات",
            "شفاط", "خلاطة اسمنت", "مضخة اسمنت", "شاحنة نفايات", "شاحنة مياه", "شاحنة وقود", 
            "شاحنة زراعية", "شاحنات خفيفة", "شاحنات متوسطة", "شاحنات ثقيلة", "شاحنات كهربائية", 
            "شاحنات جديدة", "شاحنات مستعملة", "قطع غيار شاحنات", "أخرى"
        ],
        "مقطورات": [
            "مقطورة حاويات", "مقطورة سيارات", "كرفان", "سطحة", "مقطورة صندوق", "مقطورة براد", 
            "مقطورة تنك", "مقطورة قلابة", "مقطورة منخفضة", "مقطورة ثقيلة", "مقطورة زراعية", 
            "مقطورة معدات", "مقطورة قلاب", "مقطورة جديدة", "مقطورة مستعملة", "قطع غيار مقطورات", "أخرى"
        ],
        "معدات ثقيلة": [
            "حفارات", "بلدوزر", "شيول", "باكهو", "رافعات", "كرين", "مداحل", "قريدر", "معدات طرق", 
            "معدات بناء", "معدات زراعية", "مولدات كهرباء", "ضواغط هواء", "معدات مستعملة", 
            "معدات جديدة", "قطع غيار معدات", "أخرى"
        ],
        "قطع غيار ومستلزمات": [
            "قطع غيار شاحنات", "قطع غيار باصات", "قطع غيار مقطورات", "قطع غيار معدات ثقيلة", 
            "إطارات شاحنات", "بطاريات", "زيوت وفلاتر", "أنظمة هيدروليك", "محركات", "قير", "أخرى"
        ],
        "خدمات": [
            "صيانة شاحنات", "صيانة معدات ثقيلة", "تأجير شاحنات", "تأجير باصات", "تأجير معدات", 
            "تأجير مقطورات", "نقل وشحن", "تخليص جمركي", "استيراد مركبات", "فحص فني", 
            "تمويل وتقسيط", "أخرى"
        ]
    }

    total_added = add_categories(db, parent_id, data, parent_category.icon_name, parent_category.color_hex)
    db.commit()
    db.close()
    print(f"Added {total_added} new items to 105.")

if __name__ == "__main__":
    main()

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

def update_category(db, parent_id, data):
    parent_category = db.query(Category).filter(Category.id == parent_id).first()
    
    if not parent_category:
        print(f"Parent {parent_id} not found")
        return 0

    # Delete existing children
    delete_children(db, parent_id)
    db.commit()
    print(f"Deleted old children for {parent_id}.")

    total_added = add_categories(db, parent_id, data, parent_category.icon_name, parent_category.color_hex)
    db.commit()
    print(f"Added {total_added} new items to {parent_id}.")
    return total_added

def main():
    db = SessionLocal()
    
    data_103 = {
        "دراجات نارية": ["سبورت", "كلاسيك", "اوف رود", "كروزر", "كهرباء", "صغيرة", "أخرى"],
        "سكوتر": ["سكوتر بنزين", "سكوتر كهرباء", "أخرى"],
        "دبابات": ["دباب رباعي", "دباب صحراوي", "دباب أطفال", "أخرى"],
        "قطع غيار دراجات": ["محرك", "كهرباء", "إطارات", "فرامل", "بطاريات", "أخرى"],
        "إكسسوارات دراجات": ["خوذ", "ملابس", "قفازات", "نظارات", "حقائب", "أخرى"],
        "صيانة وخدمات": ["صيانة", "تعديل", "دهان", "تركيب", "أخرى"],
        "أخرى": []
    }

    data_104 = {
        "محرك وميكانيك": ["محركات", "قير / ناقل حركة", "دفرنس", "رديتر وتبريد", "فلاتر", "مضخات", "سيور", "بواجي", "أخرى"],
        "كهرباء سيارات": ["بطاريات", "دينمو", "ستارتر", "حساسات", "كمبيوتر سيارة", "أسلاك", "إنارة", "أخرى"],
        "فرامل وتعليق": ["فحمات", "هوبات", "مساعدات", "يايات", "مقصات", "دركسون", "أخرى"],
        "إطارات وجنوط": ["إطارات", "جنوط", "إطارات شاحنات", "إطارات باصات", "ميزان وترصيص", "أخرى"],
        "هيكل وبودي": ["صدامات", "أبواب", "كبوت", "رفارف", "زجاج", "مرايا", "أخرى"],
        "إكسسوارات داخلية": ["فرش", "مسجل", "شاشات", "كاميرات", "حساسات اصطفاف", "إضاءة داخلية", "أخرى"],
        "إكسسوارات خارجية": ["زينة", "ليد", "زينون", "جناح", "دعسات", "حماية", "أخرى"],
        "زيوت ومواد صيانة": ["زيت محرك", "زيت قير", "ماء رديتر", "منظفات", "إضافات", "أخرى"],
        "قطع شاحنات وباصات": ["قطع شاحنات", "قطع باصات", "قطع مقطورات", "أخرى"],
        "أدوات وورش": ["عدة ميكانيك", "أجهزة فحص", "رافعات", "كمبروسر", "أخرى"]
    }

    data_106 = {
        "أرقام للبيع": ["رقم ثنائي", "رقم ثلاثي", "رقم رباعي", "رقم خماسي", "أخرى"],
        "أرقام مميزة": ["مكرر", "متسلسل", "مميز جداً", "VIP", "أخرى"],
        "أرقام حسب الفئة": ["خصوصي", "نقل", "حكومي", "دراجات", "أخرى"],
        "خدمات أرقام": ["نقل ملكية", "تقييم رقم", "مزاد", "تبديل", "أخرى"],
        "طلب رقم مميز": ["طلب شراء", "طلب تبديل", "أخرى"]
    }
    
    total = 0
    total += update_category(db, 103, data_103)
    total += update_category(db, 104, data_104)
    total += update_category(db, 106, data_106)
    
    print(f"Total categories added: {total}")
        
    db.close()

if __name__ == "__main__":
    main()

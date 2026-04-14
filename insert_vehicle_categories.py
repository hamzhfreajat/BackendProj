import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Category

def add_categories(db, parent_id, items, parent_icon, parent_color):
    total_added = 0
    
    # Get existing children for this parent
    existing_children = db.query(Category).filter(Category.parent_id == parent_id).all()
    existing_map = {child.name: child.id for child in existing_children}
    
    if isinstance(items, list):
        for name in items:
            if name not in existing_map:
                new_cat = Category(
                    name=name,
                    parent_id=parent_id,
                    icon_name=parent_icon,
                    color_hex=parent_color
                )
                db.add(new_cat)
                db.flush() # To get the ID if we needed it, but here it's just a leaf
                total_added += 1
    elif isinstance(items, dict):
        for name, sub_items in items.items():
            cat_id = existing_map.get(name)
            if not cat_id:
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
            
            # Recurse for subcategories
            total_added += add_categories(db, cat_id, sub_items, parent_icon, parent_color)
            
    return total_added

def main():
    db = SessionLocal()
    
    data = {
        103: [
            "سبورت (Sport)", "كروزر (Cruiser)", "تورينج / سفر (Touring)", 
            "نيكِد / ستريت (Naked / Street)", "أدڤنتشر / دوبل سبورت (Adventure / Dual-sport)", 
            "أوف-رود / موتوكروس (Off-road / Motocross)", "كلاسيك / ريترو (Classic / Vintage)", 
            "دراجات سباق (Racing)", "دراجات كهربائية (E-bike / Electric motorcycle)", 
            "سكوتر بنزين", "سكوتر كهربائي", "دراجات رباعية (ATV / UTV)", 
            "دبابات نقل / عمل (Utility 2-3-4 wheels)", "دراجات أطفال / ميني", 
            "قطع غيار ميكانيكية (محرك، قير، تعليق، تبريد)", "كهرباء وإلكترونيات (بطاريات، إنارة، ECU)", 
            "إطارات وجنوط", "عوادم وصوتيات", "زيوت وفلاتر ومواد صيانة", 
            "صناديق وحاملات وتخزين", "خوذ وملابس حماية (خوذ، جاكيت، قفازات، أحذية)", 
            "إكسسوارات (تجميل، fairings، حقائب)", "خدمات (صيانة، تركيب، فحص ما قبل الشراء)", 
            "تأجير دراجات", "تبادل / مقايضة", "أخرى"
        ],
        104: [
            "محركات وقطع ميكانيك (رؤوس اسطوانات، بساتم، أعمدة)", "ناقل حركة / قير / كلتش", 
            "نظام تعليق وامتصاص صدمات", "نظام تبريد (رادييتور، ثرموستات)", 
            "كهرباء وإلكترونيات (أسلاك، مفاتيح، بطاريات)", "نظام فرامل (أقراص، فحمات، أنابيب)", 
            "إطارات وجنوط وإطارات تشغيل خاص", "إنارة ومصابيح (أمامية، خلفية، LED، زينون)", 
            "مرايا وزجاج (إطار، أمامي، جانبي)", "أبواب وهيكل (صبغات، صدامات، رفارف)", 
            "داخلي (فرش مقاعد، تابلوه، سجاد)", "أنظمة ترفيه وملاحة (شاشات، راديو، كاميرات)", 
            "أنظمة صوت (سماعات، مضخمات)", "أنظمة أمان (إنذار، تعقب، إيموبليزر)", 
            "حساسات ووحدات ECU وبرمجيات", "سوائل وصيانة (زيوت، سائل فرامل، مبردات)", 
            "ملحقات خارجية (حاملات سقف، بساطات، غطاء)", "ملحقات داخلية (حافظات، حوامل هاتف)", 
            "أدوات ورافعات وقطع ورش", "قطع أصلية OEM", "قطع بديلة Aftermarket", 
            "قطع مستعملة / مجددة", "قطع بالجملة لتجار"
        ],
        105: {
            "باصات": [
                "باصات ركاب", "باصات صغيرة", "باصات نقل عام", "باصات مدرسية", "باصات سياحية",
                "ميكروباص / فان", "باصات كهربائية", "باصات جديدة", "باصات مستعملة", "قطع غيار باصات"
            ],
            "شاحنات": [
                "صندوق", "تنك", "براد", "راس تريلا", "ونش", "شاسيه", "قلاب", "نقل سيارات",
                "شاحنات خفيفة", "شاحنات متوسطة", "شاحنات ثقيلة", "شاحنات جديدة", "شاحنات مستعملة", "قطع غيار شاحنات"
            ],
            "مقطورات": [
                "مقطورة حاويات", "مقطورة سيارات", "كرفان", "سطحة", "مقطورة صندوق", "مقطورة تبريد",
                "مقطورة تنك", "مقطورة ثقيلة", "مقطورة زراعية", "مقطورة جديدة", "مقطورة مستعملة", "قطع غيار مقطورات"
            ],
            "معدات ثقيلة": [
                "حفارات", "بلدوزر", "شيول", "رافعات", "مداحل", "كرين", "معدات بناء", "قطع غيار معدات ثقيلة"
            ],
            "خدمات ومستلزمات": [
                "صيانة مركبات ثقيلة", "تأجير باصات", "تأجير شاحنات", "تأجير مقطورات", "تأجير معدات", 
                "نقل وشحن", "استيراد وتخليص", "أخرى"
            ]
        },
        106: [
            "أحادية (1-حرف/رقم)", "ثنائية", "ثلاثية", "رباعية", "متتالية (مثل 1234)", 
            "مكررة (مثل 1111)", "متناظرة / منسقة (مثل 1221)", "حروف + أرقام", "أرقام حكومية", 
            "أرقام خصوصي", "أرقام نقل / تجارية", "أرقام دراجات", "للبيع", "مزاد / مزايدة", 
            "تبديل / مقايضة أرقام", "طلب شراء رقم مميز (طلبات مخصصة)", "خدمات توثيق ونقل ملكية", 
            "خدمات وساطة وتقييم سعر", "مجموعات أرقام للبيع (lots)", "أرقام مخصصة للشركات / حملات إعلانية"
        ]
    }
    
    total_added = 0
    for parent_id, items in data.items():
        parent_category = db.query(Category).filter(Category.id == parent_id).first()
        if not parent_category:
            print(f"Parent category {parent_id} not found!") # Safe for console
            continue
            
        print(f"Adding subcategories for parent ID {parent_id}...") # Removed arabic to avoid encoding error
        added = add_categories(db, parent_id, items, parent_category.icon_name, parent_category.color_hex)
        total_added += added
                
    db.commit()
    print(f"Added {total_added} new categories!")
    db.close()

if __name__ == "__main__":
    import codecs
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    main()

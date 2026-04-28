import os
from database import SessionLocal
from models import City, Region
import logging

logging.basicConfig(level=logging.INFO)

universities_map = {
    "عمان": [
        "الجامعة الأردنية",
        "جامعة العلوم التطبيقية",
        "جامعة الزيتونة",
        "جامعة البترا",
        "جامعة الشرق الأوسط",
        "جامعة الإسراء",
        "جامعة الأميرة سمية",
    ],
    "إربد": [
        "جامعة اليرموك",
        "جامعة العلوم والتكنولوجيا",
        "جامعة جدارا",
        "جامعة إربد الأهلية",
    ],
    "الزرقاء": [
        "الجامعة الهاشمية",
        "جامعة الزرقاء",
    ],
    "مادبا": [
        "الجامعة الألمانية الأردنية",
        "الجامعة الأمريكية",
    ],
    "السلط": [
        "جامعة البلقاء التطبيقية",
        "جامعة عمان الأهلية",
    ],
    "الكرك": [
        "جامعة مؤتة",
    ],
    "المفرق": [
        "جامعة آل البيت",
    ],
    "جرش": [
        "جامعة جرش",
    ],
    "معان": [
        "جامعة الحسين بن طلال",
    ],
    "الطفيلة": [
        "جامعة الطفيلة التقنية",
    ],
    "العقبة": [
        "الجامعة الأردنية فرع العقبة",
        "جامعة العقبة للتكنولوجيا",
    ],
    "عجلون": [
        "جامعة عجلون الوطنية",
    ]
}

db = SessionLocal()
try:
    total_added = 0
    for city_name, unis in universities_map.items():
        city_obj = db.query(City).filter(City.name_ar == city_name).first()
        if not city_obj:
            print(f"City not found: {city_name}")
            continue
            
        for uni_name in unis:
            existing = db.query(Region).filter(
                Region.city_id == city_obj.id,
                Region.name_ar == uni_name
            ).first()
            
            if not existing:
                new_region = Region(
                    city_id=city_obj.id,
                    name_ar=uni_name,
                    name_en=uni_name # English mapping not strictly needed, fallback to AR
                )
                db.add(new_region)
                total_added += 1
                
    db.commit()
    print(f"Successfully added {total_added} university regions.")

except Exception as e:
    db.rollback()
    print(f"Error seeding universities: {e}")
finally:
    db.close()

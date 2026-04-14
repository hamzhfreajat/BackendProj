import os
import sys
import codecs

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from database import SessionLocal
from models import Category
from sqlalchemy import text

CDN = "https://raw.githubusercontent.com/filippofilip95/car-logos-dataset/master/logos/thumb"

# Arabic brand name -> slug in the car-logos-dataset
BRAND_MAP = {
    "آي إم": "im",
    "آيتو": "aito",
    "أبارث": "abarth",
    "أوبل": "opel",
    "أودي": "audi",
    "إنفينيتي": "infiniti",
    "اس دبليو ام": "swm",
    "استون مارتن": "aston-martin",
    "افاتار": "avatr",
    "اكس بينج": "xpeng",
    "اكسيد": "exeed",
    "اكيورا": "acura",
    "الفا روميو": "alfa-romeo",
    "ايران خودرو": "iran-khodro",
    "ايسوزو": "isuzu",
    "اينوس": "eneos",
    "ايه إم سي": "amc",
    "باجاني": "pagani",
    "باو": "baw",
    "بايك": "baic",
    "بروتون": "proton",
    "بريليانس": "brilliance",
    "بستيون": "bestune",
    "بنتلي": "bentley",
    "بوجاتي": "bugatti",
    "بورجوارد": "borgward",
    "بورش": "porsche",
    "بولستار": "polestar",
    "بونتياك": "pontiac",
    "بويك": "buick",
    "بي ام دبليو": "bmw",
    "بيجو": "peugeot",
    "تاتا": "tata",
    "تام": "tam",
    "تانك": "tank",
    "تيسلا": "tesla",
    "جاك": "jac",
    "جاكوار": "jaguar",
    "جاي ام اي في": "jamev",
    "جاي ام سي": "gmc",
    "جايكو": "jaecoo",
    "جريت وول": "great-wall",
    "جي أيه سي": "gac",
    "جي إم سي": "gmc",
    "جيب": "jeep",
    "جيتور": "jetour",
    "جينيسيس": "genesis",
    "داسيا": "dacia",
    "دايهاتسو": "daihatsu",
    "دايو": "daewoo",
    "دايون": "dayun",
    "دودج": "dodge",
    "دونج فينج": "dongfeng",
    "دي اف اس كي": "dfsk",
    "دي اف ام": "dfm",
    "رايزنج": "rising",
    "ربدان": "rabdan",
    "روكس": "rox",
    "رولز رویس": "rolls-royce",
    "روي": "roewe",
    "رينو": "renault",
    "زد إكس اوتو": "zx-auto",
    "زوتي": "zotye",
    "زيكر": "zeekr",
    "ساب": "saab",
    "ساتورن": "saturn",
    "سامسونج": "samsung",
    "سانغ يونغ": "ssangyong",
    "ساوايست": "soueast",
    "سايبا": "saipa",
    "سبايكر": "spyker",
    "ستيروين": "citroen",
    "سكاي ويل": "skywell",
    "سكودا": "skoda",
    "سمارت": "smart",
    "سوبارو": "subaru",
    "سوزوكي": "suzuki",
    "سيات": "seat",
    "سيريس": "seres",
    "سينوتروك": "sinotruk",
    "سيون": "scion",
    "شيري": "chery",
    "شيفروليه": "chevrolet",
    "فاو": "faw",
    "فوتون": "foton",
    "فورثينج": "forthing",
    "فولفو": "volvo",
    "فولكسفاغن": "volkswagen",
    "في جي في": "vgv",
    "فيات": "fiat",
    "فيراري": "ferrari",
    "كاديلاك": "cadillac",
    "كايي": "kayi",
    "كرايسلر": "chrysler",
    "كوبرا": "cupra",
    "كوينيجسيج": "koenigsegg",
    "لادا": "lada",
    "لامبورغيني": "lamborghini",
    "لاند روفر": "land-rover",
    "لانسيا": "lancia",
    "لكزس": "lexus",
    "لوتس": "lotus",
    "لوسيد": "lucid",
    "لوكسجين": "luxgen",
    "ليب موتور": "leapmotor",
    "ليفان": "lifan",
    "لينج بوكس": "lynk-and-co",
    "لينكولن": "lincoln",
    "ماروتي سوزوكي": "maruti-suzuki",
    "مازدا": "mazda",
    "مازيراتي": "maserati",
    "ماكسيوس": "maxus",
    "ماهيندرا": "mahindra",
    "مرسيدس بنز": "mercedes-benz",
    "مكلارين": "mclaren",
    "ميركوري": "mercury",
    "ميني": "mini",
    "نيتا": "neta",
    "هافال": "haval",
    "هامر": "hummer",
    "هاوتاي": "hawtai",
    "هونج تشي": "hongqi",
    "هوندا": "honda",
    "هونغهاي": "foxtron",
    "هيونداي": "hyundai",
    "وولينغ": "wuling",
    "ويلتميستر": "weltmeister",
    "يودو": "yudo",
    # Special combined entries
    "هونداي - Hyundai": "hyundai",
    "تويوتا - Toyota": "toyota",
    "كيا - Kia": "kia",
    "فورد - Ford": "ford",
    "نيسان - Nissan": "nissan",
    "ميتسوبيشي - Mitsubishi": "mitsubishi",
    "سيارات صينية (شانجان، جيلي، MG)": "mg",
}

# Main category images (high quality free images from Unsplash)
MAIN_CATEGORY_IMAGES = {
    1: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=256&h=256&fit=crop",  # عقارات للبيع
    2: "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=256&h=256&fit=crop",  # عقارات للإيجار
    3: "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=256&h=256&fit=crop",  # سيارات ومركبات
    4: "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=256&h=256&fit=crop",  # خدمات
    5: "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=256&h=256&fit=crop",  # إلكترونيات
    6: "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=256&h=256&fit=crop",  # أثاث ومفروشات
    7: "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=256&h=256&fit=crop",  # أزياء وملابس
    8: "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=256&h=256&fit=crop",  # أطفال ورضع
    9: "https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=256&h=256&fit=crop",  # حيوانات أليفة
    10: "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?w=256&h=256&fit=crop", # وظائف
    11: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=256&h=256&fit=crop", # تعليم
    12: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=256&h=256&fit=crop", # رياضة
    13: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=256&h=256&fit=crop", # طعام ومطاعم
}

def main():
    db = SessionLocal()
    
    # 1. Widen icon_name column to support URLs
    try:
        db.execute(text("ALTER TABLE categories ALTER COLUMN icon_name TYPE TEXT"))
        db.commit()
        print("Altered icon_name column to TEXT.")
    except Exception as e:
        db.rollback()
        print(f"Column alter skipped (may already be TEXT): {e}")
    
    updated = 0
    
    # 2. Update main category images
    for cat_id, img_url in MAIN_CATEGORY_IMAGES.items():
        cat = db.query(Category).filter(Category.id == cat_id).first()
        if cat:
            cat.icon_name = img_url
            updated += 1
    
    # 3. Update car brand logos
    brands = db.query(Category).filter(Category.parent_id.in_([100, 101])).all()
    for brand in brands:
        slug = BRAND_MAP.get(brand.name)
        if slug:
            brand.icon_name = f"{CDN}/{slug}.png"
            updated += 1
        else:
            print(f"No slug mapping for: {brand.name} (ID: {brand.id})")
    
    db.commit()
    print(f"Updated {updated} categories with image URLs.")
    db.close()

if __name__ == "__main__":
    main()

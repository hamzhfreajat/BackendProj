import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('d:/open/classifieds-app/backend/valid_locations.json', encoding='utf-8') as f:
    valid_locations = json.load(f)

with open('d:/open/classifieds-app/backend/others_chunk_4.json', encoding='utf-8') as f:
    ads = json.load(f)

def norm(text):
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[أإآآ]', 'ا', text)
    text = re.sub(r'ة\b', 'ه', text)
    text = re.sub(r'ى\b', 'ي', text)
    text = re.sub(r'[\s_,\-\./\\()|#]+', ' ', text)
    return text.strip().lower()

# Build valid locations dict
# Every location in valid_locations is "City, District"
valid_set = set(valid_locations)

# Create lookup dicts
# Map (norm_city, norm_dist) -> original valid location
city_dist_to_orig = {}
# Map norm_dist -> list of (orig, city, dist)
dist_to_origs = {}

for loc in valid_locations:
    c, d = [x.strip() for x in loc.split(',', 1)]
    nc, nd = norm(c), norm(d)
    city_dist_to_orig[(nc, nd)] = loc
    if nd not in dist_to_origs:
        dist_to_origs[nd] = []
    dist_to_origs[nd].append((loc, c, d))

# Known Jordan cities
CITIES = ["عمان", "إربد", "الزرقاء", "السلط", "مادبا", "العقبة", "المفرق", "جرش", "الكرك", "عجلون", "معان", "الطفيلة"]
NORM_CITIES = {norm(c): c for c in CITIES}

# Useful landmark / sub-district mappings to valid locations
LANDMARKS = {
    # Amman
    "دوار اقرا": "عمان, ضاحية الرشيد",
    "دوار اقرأ": "عمان, ضاحية الرشيد",
    "التعليم العالي": "عمان, الجبيهة",
    "شارع البلدية": "عمان, الجبيهة",
    "الجامعة الاردنية": "عمان, شارع الجامعة",
    "البوابة الشمالية": "عمان, الجبيهة",
    "الجامعة الأردنية": "عمان, شارع الجامعة",
    "نادي الجواد العربي": "عمان, طريق المطار",
    "ضاحية الجواد العربي": "عمان, طريق المطار",
    "دوار الأميرة بسمة": "عمان, الجبيهة",
    "مقابل الغزالي": "عمان, الجبيهة",
    "مدارس الحصاد": "عمان, البنيات",
    "متنزه غمدان": "عمان, طريق المطار",
    "إسكان الملكية": "عمان, طريق المطار",
    "اسكان الملكية": "عمان, طريق المطار",
    "دوار اليوسفي": "إربد, الحي الشرقي", # near Irbid east / Yarmouk / Amman bus station
    "مسجد المختار": "إربد, الحي الشرقي",
    "مجمع عمان الجديد": "إربد, الحي الشرقي", # Irbid Amman complex is in southern/eastern Irbid, often associated with الحي الشرقي or دوار اللوازم
    "مجمع عمان": "إربد, الحي الشرقي",
    "جامعة اليرموك": "إربد, الحي الشرقي", # Irbid Yarmouk university area
    "دوار الجامعة": "إربد, شارع الجامعة",
    "جامعة العلوم والتكنولوجيا": "إربد, جامعة العلوم والتكنولوجيا",
    "باصات التكنو": "إربد, الحي الشرقي",
    "دوار اللوازم": "إربد, دوار اللوازم",
    "اشارة الداروشة": "إربد, اشارة الدراوشة",
    "اشارة الدراوشة": "إربد, اشارة الدراوشة",
    "مطعم الطيارة": "إربد, ايدون", # ايدون / حوض الماصية
    "جويل سنتر": "إربد, ايدون",
    "حوض الماصية": "إربد, ايدون",
    "حوض ابوعوسية": "إربد, ايدون",
    "شارع ابوراشد": "إربد, ايدون",
    "شارع ابو راشد": "إربد, ايدون",
    "حلويات الاقصي": "إربد, ايدون",
    "اربد مول": "إربد, اربد مول",
    "شارع البتراء": "إربد, شارع البتراء", # Wait! Is شارع البتراء in valid_locations for Irbid? Let's check!
    "الوسط التجاري": "العقبة, المركزية",
    "السوق التجاري": "العقبة, المركزية",
    "وسط المدينة": "العقبة, المركزية",
    "واحة ايلا": "العقبة, ايلة",
    "واحة أيلة": "العقبة, ايلة",
    "ايلا": "العقبة, ايلة",
    "أيلة": "العقبة, ايلة",
    "الجبل الصامد": "العقبة, الحرفية", # Wait, check العقبة valid locs
    "حي الجزيرة": "مادبا, حي الجزيرة",
    "محطة الفلاحات": "مادبا, حي الجزيرة",
    "جامع الفردوس": "إربد, الضاحية", # or عمان? Check context
    "المناخر": "عمان, المناخر", # missing or mapped?
    "رحاب": "المفرق, ارحاب",
    "منيفة": "المفرق, ارحاب",
    "حوض ام الفول": "المفرق, ارحاب",
    "شطوره": "عجلون, شطورة",
    "شطورة": "عجلون, شطورة",
    "عنيبة": "جرش, عنبة",
    "المسامير": "الزرقاء, الزرقاء الجديدة",
    "مسبح دايموند": "الزرقاء, الزرقاء الجديدة",
}

print("Script template ready.")

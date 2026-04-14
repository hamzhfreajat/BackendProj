import re

tree_text = """
├── الدراجات ومستلزماتها (Bicycles & Cycling)
│   ├── الدراجات
│   │   ├── دراجات هوائية
│   │   ├── دراجات كهربائية
│   │   └── دراجات أطفال
│   │
│   ├── قطع الغيار والإكسسوارات
│   │   ├── قطع غيار دراجات هوائية
│   │   ├── إكسسوارات دراجات
│   │   ├── ملابس ركوب الدراجات
│   │   └── دراجات ومستلزماتها الأخرى
│
├── اللياقة البدنية وبناء الأجسام (Fitness & Bodybuilding)
│   ├── أجهزة تدريب القوة
│   │   ├── معدات تدريب القوة
│   │   ├── أوزان حرة
│   │   ├── أجهزة مقاومة وقوة
│   │   ├── مقاعد وأرفف أوزان
│   │   ├── أجهزة سحب ودفع (بار سحب ودِب)
│   │   ├── إكسسوارات تدريب القوة
│   │   └── أجهزة تدريب قوة أخرى
│   │
│   ├── أجهزة الكارديو (Cardio Training)
│   │   ├── أجهزة سير رياضي (Treadmills)
│   │   ├── دراجات تمارين
│   │   ├── أجهزة تدريب كروس وإليبتكال
│   │   ├── أجهزة تجديف
│   │   └── أجهزة كارديو أخرى
│
├── التخييم والأنشطة الخارجية (Camping & Outdoors)
│   ├── المعدات الأساسية
│   │   ├── خيام وشمسيات
│   │   ├── معدات نوم (أكياس نوم، مراتب)
│   │   ├── أثاث تخييم
│   │   └── حقائب ظهر ومستلزمات مشي
│   │
│   ├── الطهي والطاقة
│   │   ├── معدات طبخ وتسخين
│   │   └── فحم وحطب
│   │
│   ├── الأمان والملاحة
│   │   ├── معدات ملاحة وأمان
│   │   └── مياه وترشيح
│   │
│   ├── متفرقات
│   │   ├── ملابس وأحذية خارجية
│   │   ├── أدوات وإكسسوارات تخييم
│   │   └── معدات خارجية أخرى
│
├── رياضات المضرب والطاولة (Racket & Table Sports)
│   ├── ألعاب الطاولة والصالات
│   │   ├── بلياردو وسنوكر
│   │   ├── بيبي فوت (فوسبول)
│   │   ├── هوكي هواء
│   │   ├── تنس طاولة
│   │   └── لُعب السهام (دارتس)
│   │
│   ├── رياضات المضرب
│   │   ├── تنس الأرضي
│   │   ├── بادمنتون (ريشة طائرة)
│   │   ├── بادل (Padel)
│   │   ├── إسكواش
│   │   └── رياضات طاولة ومضرب أخرى
│
├── التزلج والتنقل الشخصي (Skating & Scooters)
│   ├── ألواح تزلج (سكيت بورد)
│   ├── سكوترات (عادية)
│   ├── سكوترات كهربائية
│   ├── أحذية تزلج بعجلات (رولر سكاتس)
│   └── إكسسوارات تزلج وسكوتر أخرى
│
├── الصيد والرماية (Hunting & Fishing)
│   ├── صيد الأسماك
│   │   ├── معدات صيد الأسماك
│   │   ├── إكسسوارات صيد الأسماك
│   │   └── مصائد وشباك
│   │
│   ├── الرماية وصيد البر
│   │   ├── معدات صيد
│   │   ├── إكسسوارات صيد
│   │   ├── ملابس صيد
│   │   └── صيد وصيد أسماك أخرى
│
├── رياضات الكرة (Ball Sports)
│   ├── كرة قدم
│   ├── كرة سلة
│   ├── كرة طائرة
│   ├── جولف
│   ├── بيسبول
│   └── رياضات كرة أخرى
│
├── الفنون القتالية (Martial Arts)
│   ├── ملابس وأزياء فنون قتالية
│   ├── معدات تدريب فنون قتالية
│   ├── معدات حماية فنون قتالية
│   └── فنون قتالية أخرى
│
├── الغوص والرياضات المائية (Diving & Water Sports)
│   ├── معدات غوص
│   ├── سترات نجاة وأمان
│   └── غوص ورياضات مائية أخرى
│
└── الإكسسوارات الرياضية العامة
    └── الاكسسوارات الرياضية (حقائب جيم، مشدات، أدوات قياس، إلخ)
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    name = re.sub(r'\(.*?\)', '', name).strip()
    return name

def get_icon(name):
    n = name.lower()
    if 'دراج' in n: return 'directions_bike'
    elif 'لياقة' in n or 'تدريب' in n or 'قوة' in n or 'كارديو' in n or 'أوزان' in n: return 'fitness_center'
    elif 'تخييم' in n or 'خيم' in n or 'أنشطة' in n or 'خارجي' in n: return 'terrain'
    elif 'طبخ' in n or 'فحم' in n or 'تسخين' in n: return 'outdoor_grill'
    elif 'ملاحة' in n or 'أمان' in n: return 'explore'
    elif 'مضرب' in n or 'تنس' in n or 'بادل' in n or 'إسكواش' in n or 'طاولة' in n or 'بلياردو' in n: return 'sports_tennis'
    elif 'تزلج' in n or 'سكوتر' in n: return 'skateboarding'
    elif 'صيد' in n or 'رماية' in n or 'شباك' in n: return 'my_location'
    elif 'كرة' in n or 'قدم' in n or 'سلة' in n or 'جولف' in n: return 'sports_soccer'
    elif 'فنون قتالية' in n or 'حماية' in n: return 'sports_martial_arts'
    elif 'غوص' in n or 'مائية' in n or 'نجاة' in n: return 'scuba_diving'
    elif 'إكسسوارات' in n or 'حقائب' in n or 'ملابس' in n: return 'checkroom'
    else: return 'sports'

def parse_tree(lines_text):
    gen = []
    l1_idx = 0; l2_idx = 0; l3_idx = 0
    current_l1_id = None; current_l2_id = None
    
    for line in lines_text.strip().split('\n'):
        if not line.strip() or line.strip() == '│': continue
        
        match = re.match(r'^[├└│\s─]+', line)
        if not match: continue
        prefix = match.group(0)
        
        name = clean_name(line)
        if not name: continue
        
        icon = get_icon(name)
        depth = len(prefix)
        
        if depth < 6:
            l1_idx += 1
            current_l1_id = int(f"13{l1_idx:02d}")
            gen.append(f'    ({current_l1_id}, 13, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
            l2_idx = 0; l3_idx = 0
        elif depth < 10:
            l2_idx += 1
            current_l2_id = int(f"{current_l1_id}{l2_idx:02d}")
            gen.append(f'    ({current_l2_id}, {current_l1_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
            l3_idx = 0
        else:
            l3_idx += 1
            l3_id = int(f"{current_l2_id}{l3_idx:02d}")
            gen.append(f'    ({l3_id}, {current_l2_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
            
    return gen

gen_list = parse_tree(tree_text)

generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SPORTS AND FITNESS (parent=13)',
    '    # ═══════════════════════════════════════════════',
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        break
    
    if '# SPORTS AND FITNESS (parent=' in line:
        skip = True
        
    if skip:
        continue
        
    # Overwrite the parent definition
    if '(13, None, "رياضة وتسلية"' in line or '(13,  None, "رياضة وتسلية"' in line:
        line = '    (13, None, "الرياضة، اللياقة، والأنشطة الخارجية", "أجهزة رياضية، دراجات هوائية، خيم، وأراجيل", "fitness_center", "#FF5722", None, {"en": ["Sports & Outdoors"]}),\n'
        
    out_lines.append(line)

for gl in generated:
    out_lines.append(gl + '\n')

out_lines.append(']\n\n\n')

seed_started = False
for line in lines:
    if line.startswith('def seed():'):
        seed_started = True
    
    if seed_started:
        out_lines.append(line)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(''.join(out_lines))

print(f"Total Sports categories parsed: {len(generated) - 3}")

# Also update the database root object manually immediately
from database import SessionLocal
from models import Category
db = SessionLocal()
root_cat = db.query(Category).filter_by(id=13).first()
if root_cat:
    root_cat.name = "الرياضة، اللياقة، والأنشطة الخارجية"
    db.commit()
db.close()

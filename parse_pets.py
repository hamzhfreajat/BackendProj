import re

tree_text = """
├── 🐕 كلاب
│   ├── كلاب للبيع
│   │   ├── كلاب حراسة
│   │   ├── كلاب زينة
│   │   ├── كلاب صيد
│   │   ├── كلاب عمل / بوليسية
│   │   └── أخرى
│   ├── حسب الحجم
│   │   ├── كلاب صغيرة
│   │   ├── كلاب متوسطة
│   │   ├── كلاب كبيرة
│   │   └── أخرى
│   ├── أشهر السلالات
│   │   ├── جيرمن شيبرد
│   │   ├── غولدن ريتريفر
│   │   ├── هاسكي
│   │   ├── بيتبول
│   │   ├── لولو
│   │   ├── تشيواوا
│   │   ├── روت وايلر
│   │   └── أخرى
│   ├── الفئات العمرية
│   │   ├── جراء
│   │   ├── كلاب بالغة
│   │   ├── كلاب مسنة
│   │   └── أخرى
│   ├── حالات خاصة
│   │   ├── كلاب مدربة على الطاعة
│   │   ├── كلاب مدربة على الحراسة
│   │   ├── كلاب للتبني
│   │   └── أخرى
│   └── أخرى
│       ├── خدمات تزاوج
│       ├── تصاريح اقتناء
│       ├── شرائح إلكترونية
│       └── أخرى

├── 🐈 قطط
│   ├── قطط للبيع
│   │   ├── قطط منزلية
│   │   ├── قطط نادرة
│   │   ├── قطط للعرض
│   │   └── أخرى
│   ├── أشهر السلالات
│   │   ├── شيرازي
│   │   ├── سيامي
│   │   ├── سكوتش فولد
│   │   ├── بيرمن
│   │   ├── هيمالايا
│   │   ├── أنغورا
│   │   ├── قطط بلدي
│   │   └── أخرى
│   ├── الفئات العمرية
│   │   ├── صغار قطط
│   │   ├── قطط بالغة
│   │   ├── قطط مسنة
│   │   └── أخرى
│   ├── حالات خاصة
│   │   ├── مدربة على الليتر بوكس
│   │   ├── معقمة / محصنة
│   │   ├── للتبني
│   │   └── أخرى
│   └── أخرى
│       ├── إكسسوارات تجميل
│       ├── أعشاب قطط
│       └── أخرى

├── 🦜 طيور
│   ├── أنواع الطيور
│   │   ├── ببغاوات
│   │   ├── كناري
│   │   ├── حسون
│   │   ├── بادجي
│   │   ├── زيبرا
│   │   ├── طيور الحب
│   │   └── أخرى
│   ├── حمام
│   │   ├── حمام زينة
│   │   ├── حمام زاجل
│   │   ├── حمام قلاب
│   │   ├── حمام شمسي
│   │   └── أخرى
│   ├── طيور جارحة
│   │   ├── صقور
│   │   ├── عقاب
│   │   ├── بوم
│   │   └── أخرى
│   ├── طيور مائية
│   │   ├── بط
│   │   ├── إوز
│   │   ├── بجع
│   │   └── أخرى
│   ├── مستلزمات الطيور
│   │   ├── أقفاص
│   │   ├── أعشاش
│   │   ├── مراجيح
│   │   ├── أحجار كلسية
│   │   ├── أوعية طعام وماء
│   │   └── أخرى
│   └── أخرى
│       ├── فراخ طيور
│       ├── طيور متكلمة
│       ├── حلقات تعريف
│       └── أخرى

├── 🐠 أسماك وحياة مائية
│   ├── أنواع الأسماك
│   │   ├── أسماك مياه عذبة
│   │   ├── أسماك مياه مالحة
│   │   ├── أسماك مفترسة
│   │   ├── أسماك ذهبية
│   │   └── أخرى
│   ├── أحواض السمك
│   │   ├── زجاجية
│   │   ├── أكريليك
│   │   ├── طاولات أحواض
│   │   ├── نانو
│   │   └── أخرى
│   ├── تجهيزات
│   │   ├── فلاتر
│   │   ├── مضخات
│   │   ├── سخانات
│   │   ├── إضاءة
│   │   ├── أجهزة UV
│   │   └── أخرى
│   ├── بيئة الحوض
│   │   ├── نباتات
│   │   ├── مرجان
│   │   ├── رمل وحصى
│   │   ├── ديكور
│   │   └── أخرى
│   ├── غذاء وعناية
│   │   ├── طعام
│   │   ├── طعام مجمد
│   │   ├── طعام حي
│   │   ├── أدوات قياس
│   │   └── أخرى
│   └── أخرى
│       ├── سلاحف مائية
│       ├── قواقع
│       ├── جمبري
│       └── أخرى

├── 🐹 حيوانات صغيرة وزواحف
│   ├── قوارض
│   │   ├── أرانب
│   │   ├── هامستر
│   │   ├── خنازير غينيا
│   │   ├── سناجب
│   │   ├── فيرّيت
│   │   ├── جربوع
│   │   └── أخرى
│   ├── زواحف وبرمائيات
│   │   ├── سلاحف
│   │   ├── إيغوانا
│   │   ├── حرباء
│   │   ├── ثعابين
│   │   ├── ضفادع
│   │   └── أخرى
│   ├── مستلزمات
│   │   ├── بيوت
│   │   ├── عجلات
│   │   ├── نشارة
│   │   ├── رمل
│   │   └── أخرى
│   └── أخرى
│       ├── عناكب
│       ├── عقارب
│       └── أخرى

├── 🐣 حيوانات مزرعة صغيرة
│   ├── طيور مزرعة
│   │   ├── دجاج
│   │   ├── صوص
│   │   ├── بط
│   │   ├── إوز
│   │   ├── ديك رومي
│   │   └── أخرى
│   ├── أرانب
│   ├── مستلزمات
│   │   ├── فقاسات
│   │   ├── مشارب
│   │   ├── معالف
│   │   ├── حظائر
│   │   └── أخرى
│   └── أخرى
│       ├── ماعز قزم
│       ├── سمان
│       └── أخرى

├── 🍖 مستلزمات الطعام والتغذية
│   ├── طعام
│   │   ├── جاف
│   │   ├── رطب
│   │   ├── طبيعي
│   │   └── أخرى
│   ├── مكافآت
│   ├── أدوات إطعام
│   ├── تخزين طعام
│   └── أخرى

├── 🧼 العناية والنظافة
│   ├── استحمام وتجميل
│   ├── أدوات عناية
│   ├── نظافة المكان
│   └── أخرى

├── 🏠 السكن والنقل
│   ├── أسرّة
│   ├── بيوت
│   ├── أقفاص
│   ├── شنط نقل
│   ├── صناديق نقل
│   └── أخرى

├── ⛓️ التدريب والسير
│   ├── أطواق
│   ├── سلاسل
│   ├── أحزمة
│   ├── أدوات تدريب
│   └── أخرى

├── 🎾 ألعاب وترفيه
│   ├── ألعاب تفاعلية
│   ├── ألعاب حركة
│   ├── أثاث لعب
│   └── أخرى

├── 🚑 الصحة والعلاج
│   ├── أدوية
│   ├── وقاية
│   ├── إسعافات أولية
│   ├── مستلزمات طبية
│   └── أخرى

├── 👔 ملابس وإكسسوارات
│   ├── ملابس
│   ├── إكسسوارات
│   └── أخرى

├── 👨⚕️ خدمات الحيوانات
│   ├── خدمات طبية
│   ├── رعاية وفندقة
│   ├── تجميل
│   └── أخرى

└── 📦 أخرى
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    return "".join(c for c in name if c.isalnum() or c.isspace() or c in "/-.").strip()

def get_icon(name):
    n = name.lower()
    if 'قطط' in n or 'كلاب' in n or 'تبني' in n or 'سلال' in n or 'عمر' in n: return 'pets'
    elif 'طيور' in n or 'حمام' in n or 'صقور' in n or 'دجاج' in n or 'فراخ' in n or 'صوص' in n or 'بوم' in n: return 'flutter_dash'
    elif 'مائية' in n or 'أسماك' in n or 'حوض' in n or 'فلاتر' in n or 'مضخ' in n or 'سمك' in n or 'بحر' in n: return 'water'
    elif 'قوارض' in n or 'أرانب' in n or 'هامستر' in n or 'سناجب' in n or 'خنزير' in n: return 'cruelty_free'
    elif 'زواحف' in n or 'سلاحف' in n or 'ثعابين' in n or 'ضفادع' in n or 'حشرات' in n or 'عناكب' in n: return 'bug_report'
    elif 'طعام' in n or 'تغذية' in n or 'مكافآت' in n or 'أكل' in n or 'معالف' in n: return 'restaurant'
    elif 'عناية' in n or 'نظافة' in n or 'استحمام' in n or 'شامبو' in n or 'رمل' in n: return 'clean_hands'
    elif 'سكن' in n or 'بيوت' in n or 'أقفاص' in n or 'أسرّة' in n or 'حظائر' in n or 'نقل' in n: return 'house'
    elif 'تدريب' in n or 'سلاسل' in n or 'أطواق' in n or 'أحزمة' in n: return 'fitness_center'
    elif 'ألعاب' in n or 'ترفيه' in n or 'لعب' in n: return 'toys'
    elif 'صحة' in n or 'علاج' in n or 'أدوية' in n or 'وقاية' in n or 'طبية' in n or 'إسعاف' in n: return 'medical_services'
    elif 'ملابس' in n or 'إكسسوارات' in n: return 'checkroom'
    elif 'خدمات' in n or 'تزاوج' in n or 'رعاية' in n or 'تجميل' in n: return 'support_agent'
    else: return 'pets'

def parse_tree(lines_text):
    gen = []
    l1_idx = 0; l2_idx = 0; l3_idx = 0
    current_l1_id = None; current_l2_id = None
    
    for line in lines_text.strip().split('\n'):
        if not line.strip(): continue
        
        match = re.match(r'^[├└│\s─]+', line)
        if not match: continue
        prefix = match.group(0)
        
        name = clean_name(line)
        icon = get_icon(name)
        depth = len(prefix)
        
        if depth < 6:
            l1_idx += 1
            current_l1_id = int(f"12{l1_idx:02d}")
            gen.append(f'    ({current_l1_id}, 12, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
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
    '    (12, None, "حيوانات أليفة", "قطط، كلاب، طيور، وأسماك زينة", "pets", "#8BC34A", None, {"en": ["Pets"]}),',
    '    # ═══════════════════════════════════════════════',
    '    # PETS AND ANIMALS (parent=12)',
    '    # ═══════════════════════════════════════════════',
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        break
    
    if '# PETS AND ANIMALS (parent=12)' in line:
        skip = True
        
    if skip:
        continue
        
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

print(f"Total Pets categories parsed: {len(generated) - 3}")


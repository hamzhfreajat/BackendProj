import re

tree_text = """
├── 🍼 حديثي الولادة (0 - 12 شهر)
│   ├── ملابس مواليد
│   │   ├── بربتوزات
│   │   ├── أطقم خروج
│   │   ├── ملابس نوم / بجامات
│   │   ├── قبعات وقفازات
│   │   ├── جوارب
│   │   ├── كافولة / مهاد
│   │   └── أخرى
│   ├── بطانيات ومفارش
│   │   ├── بطانيات خفيفة
│   │   ├── بطانيات شتوية
│   │   ├── شراشف سرير
│   │   ├── وسائد حماية الرأس
│   │   ├── مفارش تغيير الحفاض
│   │   └── أخرى
│   ├── حفاضات
│   │   ├── حفاضات استعمال مرة واحدة
│   │   ├── حفاضات قماشية
│   │   ├── حفاضات سباحة
│   │   └── أخرى
│   ├── مناديل مبللة
│   │   ├── مناديل مائية
│   │   ├── مناديل معطرة
│   │   ├── مناديل للبشرة الحساسة
│   │   └── أخرى
│   ├── رضاعة وحليب أطفال
│   │   ├── رضاعات
│   │   ├── حلمات رضاعة
│   │   ├── حليب بودرة
│   │   ├── أجهزة تسخين الرضاعات
│   │   ├── فرش تنظيف
│   │   └── أخرى
│   ├── لهايات
│   │   ├── لهايات سيليكون
│   │   ├── مشابك لهاية
│   │   ├── علب حفظ
│   │   └── أخرى
│   ├── أدوات تعقيم
│   │   ├── جهاز تعقيم بالبخار
│   │   ├── جهاز تعقيم UV
│   │   ├── أقراص تعقيم
│   │   └── أخرى
│   ├── أدوات استحمام
│   │   ├── بانيو
│   │   ├── إسفنج
│   │   ├── ميزان حرارة الماء
│   │   ├── كرسي استحمام
│   │   └── أخرى
│   ├── مناشف أطفال
│   │   ├── مناشف بغطاء رأس
│   │   ├── أرواب
│   │   ├── مناشف وجه
│   │   └── أخرى
│   ├── أسرّة أطفال
│   │   ├── سرير خشبي
│   │   ├── سرير هزاز
│   │   ├── مهد جانبي
│   │   └── أخرى
│   ├── مهد / سرير متنقل
│   │   ├── سرير سفر
│   │   ├── سرير قابل للطي
│   │   └── أخرى
│   ├── عربات أطفال
│   │   ├── عربة كاملة
│   │   ├── عربة خفيفة
│   │   ├── مظلة عربة
│   │   └── أخرى
│   ├── مقاعد سيارة
│   │   ├── كرسي مواليد
│   │   ├── قاعدة كرسي
│   │   └── أخرى
│   ├── حقائب أمومة
│   │   ├── حقيبة ظهر
│   │   ├── حقيبة تنظيم
│   │   ├── حقيبة حرارية
│   │   └── أخرى
│   ├── أجهزة مراقبة الطفل
│   │   ├── كاميرا
│   │   ├── جهاز صوتي
│   │   ├── جهاز تنفس
│   │   └── أخرى
│   └── ألعاب مواليد
│       ├── شخاليل
│       ├── ألعاب سرير
│       ├── حصيرة ألعاب
│       ├── عضاضات
│       └── أخرى

├── 🧒 الرضع (1 - 3 سنوات)
│   ├── ملابس
│   ├── أحذية
│   ├── ألعاب تعليمية
│   ├── ألعاب ترفيهية
│   ├── كراسي طعام
│   ├── أدوات أكل
│   ├── أكواب تدريب
│   ├── تدريب حمام
│   ├── مقاعد سيارة
│   ├── عربات
│   ├── أسِرّة وحماية
│   ├── أمان المنزل
│   ├── حقائب طعام
│   └── أخرى

├── 👦 الأطفال (4 - 10 سنوات)
│   ├── ملابس
│   ├── أحذية
│   ├── حقائب مدرسية
│   ├── أدوات مدرسية
│   ├── ألعاب
│   ├── ألعاب إلكترونية
│   ├── دراجات
│   ├── سكوترات
│   ├── أثاث غرف
│   ├── أدوات رسم
│   ├── كتب وقصص
│   └── أخرى

├── 🧑🎤 المراهقين (11 - 16 سنة)
│   ├── ملابس
│   ├── أحذية
│   ├── حقائب
│   ├── أدوات مدرسية
│   ├── أجهزة إلكترونية
│   ├── ألعاب فيديو
│   ├── معدات رياضية
│   ├── دراجات وسكوترات
│   ├── أثاث غرف
│   ├── كتب تعليمية
│   └── أخرى

├── 🛏️ أثاث ومستلزمات الأطفال
│   ├── أسرّة
│   ├── خزائن
│   ├── مكاتب
│   ├── كراسي
│   ├── طاولات
│   ├── تخزين
│   ├── ديكور غرف
│   └── أخرى

├── 🏥 صحة وعناية الأطفال
│   ├── مستحضرات عناية
│   ├── شامبو وصابون
│   ├── كريمات
│   ├── ميزان حرارة
│   ├── أجهزة طبية
│   ├── فيتامينات
│   └── أخرى

├── 🎒 مستلزمات المدرسة
│   ├── حقائب
│   ├── دفاتر وقرطاسية
│   ├── أدوات كتابة
│   ├── لانش بوكس
│   ├── زجاجات ماء
│   ├── زي مدرسي
│   └── أخرى

├── 🎮 ألعاب وترفيه
│   ├── ألعاب تعليمية
│   ├── ألعاب تركيب
│   ├── دمى
│   ├── سيارات ألعاب
│   ├── ألعاب خارجية
│   ├── مسابح أطفال
│   ├── ألعاب إلكترونية
│   └── أخرى

├── 🤰 مستلزمات الحوامل
│   ├── وسائد حمل
│   ├── ملابس حمل
│   ├── كريمات
│   └── أخرى

├── 🎁 هدايا
│   ├── أطقم مواليد
│   ├── صناديق هدايا
│   └── أخرى

├── ✈️ معدات سفر للأطفال
│   ├── كراسي سفر
│   ├── مظلات سيارة
│   └── أخرى

├── 🎉 أدوات احتفالات
│   ├── زينة
│   ├── ملابس تنكرية
│   └── أخرى

└── 📦 أخرى
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    return "".join(c for c in name if c.isalnum() or c.isspace() or c in "/-.").strip()

def get_icon(name):
    n = name.lower()
    if 'ملابس' in n or 'بربتوز' in n or 'أزياء' in n or 'بجامات' in n or 'قبعات' in n or 'جوارب' in n or 'كافولة' in n or 'زي' in n: return 'checkroom'
    elif 'ألعاب' in n or 'شخاليل' in n or 'حصيرة' in n or 'عضاضات' in n or 'دمى' in n or 'سيارات ألعاب' in n: return 'toys'
    elif 'حفاضات' in n or 'مناديل' in n or 'رضاعة' in n or 'لهايات' in n or 'تدريب حمام' in n: return 'baby_changing_station'
    elif 'أسرّة' in n or 'سرير' in n or 'مهد' in n or 'أثاث' in n or 'ديكور' in n or 'خزائن' in n: return 'crib'
    elif 'مستلزمات' in n or 'أدوات أكل' in n or 'طعام' in n or 'أكواب' in n or 'استحمام' in n or 'بانيو' in n or 'شامبو' in n or 'صابون' in n: return 'child_friendly'
    elif 'مدرسة' in n or 'مدرسية' in n or 'حقائب' in n or 'قرطاسية' in n or 'دفاتر' in n or 'رسم' in n or 'كتب' in n: return 'school'
    elif 'سيارة' in n or 'كرسي سيارة' in n: return 'car_crash'
    elif 'عربات' in n or 'مظلة' in n: return 'stroller'
    elif 'أحذية' in n or 'سكوتر' in n or 'دراجة' in n or 'رياضة' in n: return 'directions_bike'
    elif 'كمبيوتر' in n or 'إلكتروني' in n or 'فيديو' in n: return 'videogame_asset'
    elif 'صحة' in n or 'عناية' in n or 'حرارة' in n or 'كريمات' in n or 'أجهزة طبية' in n or 'فيتامينات' in n or 'تعقيم' in n: return 'medical_services'
    elif 'حوامل' in n or 'أمومة' in n: return 'pregnant_woman'
    elif 'هدايا' in n: return 'card_giftcard'
    elif 'احتفالات' in n or 'زينة' in n or 'تنكر' in n: return 'celebration'
    elif 'سفر' in n: return 'flight'
    elif 'مواليد' in n or 'رضع' in n: return 'child_care'
    elif 'مراهق' in n: return 'face'
    else: return 'child_friendly'

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
            current_l1_id = int(f"11{l1_idx:02d}")
            gen.append(f'    ({current_l1_id}, 11, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
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
    '    (11, None, "مستلزمات أطفال", "عربايات، ملابس، ألعاب، وأسرّة أطفال", "child_friendly", "#FFC107", None, {"en": ["Baby & Kids Supplies"]}),',
    '    # ═══════════════════════════════════════════════',
    '    # BABY AND KIDS SUPPLIES (parent=11)',
    '    # ═══════════════════════════════════════════════',
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        break
    
    if '# BABY AND KIDS SUPPLIES (parent=11)' in line:
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

print(f"Total Baby & Kids categories parsed: {len(generated) - 3}")


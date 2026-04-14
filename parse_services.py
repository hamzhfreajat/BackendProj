import re

tree_text = """
├── الصحة والجمال
│   ├── مراكز طبية
│   ├── تجميل وعناية
│   ├── رعاية منزلية
│   ├── علاج طبيعي ومساج
│   ├── تغذية
│   ├── صحة نفسية
│   ├── تمريض منزلي
│   ├── علاج نطق وتخاطب
│   ├── علاج وظيفي
│   └── خدمات صحية أخرى
│
├── الأعمال والمهن
│   ├── قانونية
│   ├── محاسبة وضرائب
│   ├── استشارات تجارية
│   ├── موارد بشرية
│   ├── ترجمة وكتابة
│   ├── تسويق وإعلان
│   ├── طباعة وتصميم
│   ├── إدارة أعمال
│   ├── تطوير أعمال
│   ├── دراسات جدوى
│   ├── استشارات إدارية
│   └── خدمات مهنية أخرى
│
├── تكنولوجيا المعلومات والتقنية
│   ├── برمجة وتطوير
│   ├── أمن سيبراني
│   ├── دعم فني
│   ├── تطوير تطبيقات موبايل
│   ├── تطوير مواقع إلكترونية
│   ├── قواعد بيانات
│   ├── شبكات واتصالات
│   ├── استضافة وسيرفرات
│   ├── تحليل بيانات وذكاء أعمال
│   ├── صيانة أنظمة
│   └── خدمات تقنية أخرى
│
├── الإنشاءات والمقاولات
│   ├── بناء وخرسانة
│   ├── تصميم داخلي
│   ├── أعمال حفر وهدم
│   ├── أعمال واجهات
│   ├── عزل
│   ├── زجاج وألمنيوم
│   ├── خدمات مساحة وتخمين
│   ├── تشطيبات
│   ├── ديكور داخلي وخارجي
│   ├── تمديدات وإنشاءات عامة
│   ├── جبصين وجبس بورد
│   └── مقاولات وخدمات بناء أخرى
│
├── النقل واللوجستيات
│   ├── نقل عفش وتغليف
│   ├── توصيل ودليفيري
│   ├── نقل مياه
│   ├── نقل ديزل
│   ├── شحن دولي
│   ├── شحن محلي
│   ├── تخليص جمركي
│   ├── تخزين ومستودعات
│   ├── نقل بضائع
│   ├── تأجير شاحنات
│   └── خدمات لوجستية أخرى
│
├── التنظيف والغسيل
│   ├── تنظيف مباني ومنازل
│   ├── مكافحة حشرات
│   ├── غسيل وكوي ملابس
│   ├── تنظيف مكاتب
│   ├── تنظيف سجاد ومفروشات
│   ├── تنظيف خزانات
│   ├── تنظيف واجهات
│   ├── تنظيف بعد البناء
│   └── خدمات تنظيف أخرى
│
├── الصيانة والأعمال اليدوية
│   ├── دهان
│   ├── سباكة
│   ├── كهرباء
│   ├── نجارة
│   ├── حدادة
│   ├── تنجيد
│   ├── بلاط
│   ├── خياطة
│   ├── صيانة أبواب ونوافذ
│   ├── جبصين
│   ├── تركيب أثاث
│   ├── صيانة عامة
│   └── أعمال يدوية أخرى
│
├── صيانة الإلكترونيات
│   ├── موبايل وتابلت
│   ├── كمبيوتر
│   ├── ألعاب فيديو
│   ├── ستالايت
│   ├── شاشات
│   ├── مكيفات
│   ├── أجهزة منزلية كبيرة
│   ├── أجهزة منزلية صغيرة
│   ├── مصاعد
│   ├── أنظمة أمن ومراقبة
│   ├── كاميرات مراقبة
│   ├── طابعات وملحقات
│   ├── أجهزة صوتيات
│   └── صيانة إلكترونيات أخرى
│
├── تنسيق الحدائق
│   ├── تنسيق وصيانة حدائق
│   ├── مظلات
│   ├── برك ونوافير
│   ├── قص وتقليم أشجار
│   ├── زراعة وري
│   ├── شبكات ري
│   ├── مكافحة آفات حدائق
│   ├── تصميم حدائق
│   └── خدمات حدائق خارجية أخرى
│
├── المركبات
│   ├── صيانة وإصلاح
│   ├── ونش وسطحات
│   ├── غسيل وتلميع
│   ├── فحص فني
│   ├── كهرباء سيارات
│   ├── ميكانيك
│   ├── سمكرة ودهان
│   ├── تبديل إطارات
│   ├── كراجات
│   ├── برمجة مفاتيح
│   └── خدمات مركبات أخرى
│
├── رعاية المنزل والحيوانات
│   ├── حضانات
│   ├── رعاية مسنين
│   ├── جليسات أطفال
│   ├── جليسة منزل
│   ├── تنظيف ورعاية منزلية
│   ├── بيطرية
│   ├── تدريب وترويض
│   ├── إيواء وعناية بالحيوانات
│   ├── تمشية الحيوانات
│   └── خدمات حيوانات أخرى
│
├── الفعاليات والمناسبات
│   ├── تنظيم
│   ├── تصوير
│   ├── قاعات
│   ├── زهور
│   ├── ضيافة
│   ├── خيام ولوازم أعراس
│   ├── صوتيات وإضاءة
│   ├── دي جي وترفيه
│   ├── كاترينج
│   ├── ديكورات مناسبات
│   └── خدمات مناسبات أخرى
│
└── التعليم والتدريب
    ├── تدريس خصوصي
    ├── دورات تدريبية
    ├── تعليم لغات
    ├── تعليم مهارات
    ├── تدريب مهني
    ├── دورات تقنية
    ├── دورات إدارية
    ├── تدريب أطفال
    ├── تدريب أونلاين
    └── خدمات تعليمية أخرى
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    name = re.sub(r'\(.*?\)', '', name).strip()
    return name

def get_icon(name):
    n = name.lower()
    if 'صحة' in n or 'طب' in n or 'علاج' in n or 'تمريض' in n or 'نفسية' in n: return 'medical_services'
    elif 'جمال' in n or 'تجميل' in n: return 'spa'
    elif 'أعمال' in n or 'محاسبة' in n or 'إدارة' in n or 'تسويق' in n or 'قانونية' in n: return 'business_center'
    elif 'تكنولوجيا' in n or 'برمجة' in n or 'تطوير' in n or 'ويب' in n or 'موبايل' in n or 'مواقع' in n: return 'computer'
    elif 'إنشاءات' in n or 'بناء' in n or 'مقاولات' in n or 'حفر' in n or 'تشطيب' in n: return 'architecture'
    elif 'نقل' in n or 'لوجستيات' in n or 'ترانزيت' in n or 'شحن' in n or 'شاحنات' in n or 'عفش' in n: return 'local_shipping'
    elif 'تنظيف' in n or 'غسيل' in n or 'كوي' in n or 'مكافحة' in n or 'سجاد' in n: return 'cleaning_services'
    elif 'صيانة' in n or 'سباكة' in n or 'كهرباء' in n or 'نجارة' in n or 'حدادة' in n or 'دهان' in n: return 'handyman'
    elif 'إلكترونيات' in n or 'مكيفات' in n or 'كمبيوتر' in n or 'ساتلايت' in n or 'كاميرات' in n: return 'electrical_services'
    elif 'حدائق' in n or 'زراعة' in n or 'ري' in n or 'مظلات' in n or 'أشجار' in n: return 'deck'
    elif 'مركبات' in n or 'سيارات' in n or 'ونش' in n or 'ميكانيك' in n or 'سمكرة' in n: return 'car_repair'
    elif 'رعاية' in n or 'حيوانات' in n or 'بيطرية' in n or 'مسنين' in n or 'جليسة' in n: return 'volunteer_activism'
    elif 'فعاليات' in n or 'مناسبات' in n or 'تصوير' in n or 'قاعات' in n or 'دي جي' in n or 'أعراس' in n: return 'event'
    elif 'تعليم' in n or 'تدريب' in n or 'دورات' in n or 'لغات' in n or 'تدريس' in n: return 'school'
    else: return 'miscellaneous_services'

def parse_tree_dynamic(lines_text):
    gen = []
    level_counters = {1: 0, 2: 0, 3: 0}
    level_ids = {0: "8"}
    
    for line in lines_text.strip().split('\n'):
        if not line.strip() or line.strip() == '│': continue
        
        match = re.match(r'^[├└│\s─]+', line)
        if not match: continue
        prefix = match.group(0)
        
        name = clean_name(line)
        if not name: continue
        
        # "├── " is length 4
        # "│   ├── " is length 8
        depth = len(prefix) // 4
        if depth not in level_counters:
            depth = 1 # Fallback
            
        icon = get_icon(name)
        
        level_counters[depth] += 1
        # reset deeper
        for d in range(depth + 1, 4):
            if d in level_counters:
                level_counters[d] = 0
                
        parent_id = level_ids[depth - 1]
        my_id = f"{parent_id}{level_counters[depth]:02d}"
        level_ids[depth] = my_id
        
        gen.append(f'    ({int(my_id)}, {parent_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
            
    return gen

gen_list = parse_tree_dynamic(tree_text)

generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SERVICES (parent=8)',
    '    # ═══════════════════════════════════════════════',
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        break
    
    if '# SERVICES (parent=8)' in line:
        skip = True
        
    if skip:
        continue
        
    # Overwrite the parent definition if it is 8
    if '(8, None, "خدمات"' in line or '(8,  None, "خدمات"' in line:
        line = '    (8, None, "الخدمات", "مقاولات، صيانة، نقل عفش، وخدمات عامة", "handyman", "#607D8B", None, {"en": ["Services"]}),\n'
        
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

print(f"Total Services categories parsed: {len(generated) - 3}")

# Clean up old DB nodes physically
from database import SessionLocal
from models import Category
db = SessionLocal()

# We purge 800 - 899000 if they exist (except 8 of course)
old_cats = db.query(Category).filter(Category.id >= 800, Category.id < 9000000).all()
for c in old_cats: db.delete(c)
db.commit()

root_cat = db.query(Category).filter_by(id=8).first()
if root_cat:
    root_cat.name = "الخدمات"
    db.commit()
db.close()

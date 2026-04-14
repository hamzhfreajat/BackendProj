import re

tree_text = """
├── الجمال والعناية (Beauty & Care) 
│
│   ├── المكياج (Makeup)
│   │   ├── مكياج الوجه
│   │   │   ├── فاونديشن وكريم أساس
│   │   │   ├── بودرة
│   │   │   ├── برونزر
│   │   │   ├── هايلايتر
│   │   │   ├── برايمر
│   │   │   ├── كونسيلر
│   │   │   ├── مثبت مكياج (Setting Spray/Powder) ⭐
│   │   │   ├── أحمر خدود (Blush) ⭐
│   │   │   ├── كونتور ⭐
│   │   │   ├── مزيل مكياج
│   │   │   └── منتجات أخرى للوجه
│   │   │
│   │   ├── مكياج العيون والحواجب
│   │   │   ├── ظلال عيون
│   │   │   ├── مسكارا
│   │   │   ├── وصلات رموش
│   │   │   ├── كحلة
│   │   │   ├── آيلاينر ⭐
│   │   │   ├── أقلام حواجب
│   │   │   ├── جل حواجب ⭐
│   │   │   ├── إكسسوارات العيون ⭐
│   │   │   └── منتجات أخرى للعيون
│   │   │
│   │   ├── مكياج الشفاه
│   │   │   ├── أحمر شفاه
│   │   │   ├── ملمع شفاه
│   │   │   ├── محدد شفاه
│   │   │   ├── مرطب شفاه ⭐
│   │   │   └── منتجات أخرى للشفاه
│   │   │
│   │   └── أدوات وفرش المكياج
│   │       ├── فراشي مكياج
│   │       ├── إسفنجات
│   │       ├── ملقط
│   │       ├── مبراة ⭐
│   │       ├── منظمات مستحضرات تجميل
│   │       ├── مرايا
│   │       └── أدوات تجميلية أخرى
│   │
│   ├── العناية بالأظافر (Nail Care)
│   │   ├── طلاء أظافر
│   │   ├── مزيل طلاء أظافر ⭐
│   │   ├── ملمع أظافر
│   │   ├── تصميم وفن الأظافر
│   │   ├── وصلات وأظافر صناعية
│   │   ├── أدوات الأظافر (قصاصات ومبرد)
│   │   ├── مطهرات
│   │   └── منتجات أخرى للأظافر
│   │
│   ├── العطور والبخور (Fragrances & Incense)
│   │   ├── عطور رجالية
│   │   ├── عطور نسائية
│   │   ├── عطور أطفال
│   │   ├── زيوت عطرية
│   │   ├── العود والبخور
│   │   ├── معطرات جسم ⭐
│   │   └── معطرات منزل ⭐
│   │
│   ├── العناية بالبشرة ⭐
│   │   ├── غسول الوجه
│   │   ├── كريمات ترطيب
│   │   ├── واقي شمس
│   │   ├── سيروم
│   │   ├── مقشرات
│   │   ├── ماسكات الوجه
│   │   └── منتجات أخرى للبشرة
│   │
│   ├── العناية بالشعر ⭐
│   │   ├── شامبو وبلسم
│   │   ├── زيوت شعر
│   │   ├── صبغات شعر
│   │   ├── ماسكات وعلاجات
│   │   ├── أدوات تصفيف (سيشوار/مكواة) ⭐
│   │   └── منتجات أخرى للشعر
│   │
│   └── العناية الشخصية ⭐
│       ├── مزيلات عرق
│       ├── أدوات حلاقة
│       ├── العناية بالفم والأسنان
│       └── منتجات أخرى
│
├── الأزياء (Fashion)
│
│   ├── الأزياء النسائية
│   │   ├── الملابس النسائية
│   │   │   ├── فساتين
│   │   │   ├── بلايز وقمصان
│   │   │   ├── بناطيل وتنورات
│   │   │   ├── ملابس نوم ولانجري
│   │   │   ├── ملابس داخلية ⭐
│   │   │   ├── عبايات وجلابيات
│   │   │   ├── ملابس رياضية
│   │   │   ├── ملابس سباحة
│   │   │   ├── جاكيتات وسترات
│   │   │   └── أطقم وجمبسوت
│   │   │
│   │   ├── الأحذية النسائية
│   │   │   ├── أحذية كعب
│   │   │   ├── فلات وباليه
│   │   │   ├── أحذية رياضية (سنيكرز)
│   │   │   ├── صنادل
│   │   │   ├── بوت
│   │   │   ├── شباشب وفليب فلوب
│   │   │   ├── أحذية منزلية
│   │   │   └── أحذية أخرى
│   │   │
│   │   └── الإكسسوارات النسائية
│   │       ├── ساعات
│   │       ├── حقائب وشنط
│   │       ├── مجوهرات
│   │       ├── نظارات شمسية
│   │       ├── إكسسوارات شعر
│   │       ├── محافظ ⭐
│   │       ├── أحزمة ⭐
│   │       └── إكسسوارات أخرى
│
│   ├── الأزياء الرجالية
│   │   ├── الملابس الرجالية
│   │   │   ├── بدلات رسمية
│   │   │   ├── قمصان
│   │   │   ├── بلايز
│   │   │   ├── جاكيتات ومعاطف
│   │   │   ├── بناطيل وشورتات ⭐
│   │   │   ├── شماغ وحطة
│   │   │   ├── ملابس رياضية
│   │   │   ├── ملابس نوم
│   │   │   ├── ملابس داخلية ⭐
│   │   │   └── ربطات عنق وأوشحة
│   │   │
│   │   ├── الأحذية الرجالية
│   │   │   ├── أحذية رسمية
│   │   │   ├── أحذية رياضية
│   │   │   ├── صنادل
│   │   │   ├── بوت
│   │   │   ├── شباشب
│   │   │   └── أحذية منزلية
│   │   │
│   │   └── الإكسسوارات الرجالية
│   │       ├── ساعات
│   │       ├── نظارات شمسية
│   │       ├── محافظ
│   │       ├── أحزمة
│   │       ├── خواتم ومسابح
│   │       ├── أقلام وولاعات
│   │       ├── حقائب ⭐
│   │       └── إكسسوارات أخرى
│
├── عالم الطفل (Kids & Baby)
│
│   ├── أزياء الأطفال
│   │   ├── البنات
│   │   │   ├── ملابس
│   │   │   ├── أحذية
│   │   │   └── إكسسوارات
│   │   │
│   │   ├── الأولاد
│   │   │   ├── ملابس
│   │   │   ├── أحذية
│   │   │   └── إكسسوارات
│   │   │
│   │   └── المواليد والرضع
│   │       ├── ملابس
│   │       ├── أحذية
│   │       └── إكسسوارات
│
│   └── مستلزمات الرضع (Baby Gear)
│       ├── التغذية والرضاعة
│       │   ├── رضاعات
│       │   ├── معقمات ومسخنات
│       │   ├── شفاطات حليب
│       │   ├── وسائد رضاعة ⭐
│       │   ├── كراسي طعام
│       │   ├── أدوات وأطباق
│       │   ├── أجهزة تحضير الطعام
│       │   └── مستلزمات أخرى
│       │
│       ├── التنقل والسفر
│       │   ├── عربات أطفال
│       │   │   ├── عربات توائم
│       │   │   ├── عربات عادية
│       │   │   ├── عربات سفر
│       │   │   └── ملحقات العربات
│       │   ├── مقاعد سيارة
│       │   └── حمالات بيبي
│       │
│       ├── الأنشطة واللعب
│       │   ├── مشايات
│       │   ├── هزازات
│       │   ├── أرجوحات
│       │   └── ألعاب تنمية المهارات ⭐
│       │
│       ├── النوم والمنسوجات
│       │   ├── بطانيات
│       │   ├── مفارش سرير
│       │   ├── مناشف
│       │   ├── وسائد ⭐
│       │   └── منتجات أخرى
│       │
│       └── العناية والنظافة
│           ├── حفاضات
│           ├── مناديل مبللة
│           ├── منتجات الاستحمام
│           ├── العناية بالفم
│           ├── العناية بالشعر
│           └── منتجات نظافة أخرى
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    name = re.sub(r'\(.*?\)', '', name).strip()
    name = name.replace('⭐', '').strip()
    return name

def get_icon(name):
    n = name.lower()
    if 'مكياج' in n or 'وجه' in n or 'شفاه' in n or 'عيون' in n or 'بشرة' in n or 'جمال' in n: return 'face_retouching_natural'
    elif 'شعر' in n or 'عناية' in n or 'حلاقة' in n or 'استحمام' in n or 'شامبو' in n: return 'spa'
    elif 'عطر' in n or 'بخور' in n or 'عود' in n or 'عطور' in n: return 'air'
    elif 'أظافر' in n: return 'pan_tool'
    elif 'ملابس' in n or 'أزياء' in n or 'فساتين' in n or 'قمصان' in n: return 'checkroom'
    elif 'أحذية' in n or 'صنادل' in n or 'بوت' in n: return 'snowshoeing'
    elif 'إكسسوار' in n or 'حقائب' in n or 'شنط' in n or 'مجوهرات' in n or 'محافظ' in n: return 'shopping_bag'
    elif 'ساعات' in n: return 'watch'
    elif 'طفل' in n or 'أطفال' in n or 'مواليد' in n or 'رضع' in n or 'بنات' in n or 'أولاد' in n: return 'child_care'
    elif 'تغذية' in n or 'رضاع' in n or 'طعام' in n: return 'restaurant'
    elif 'عربات' in n or 'تنقل' in n or 'مقاعد سيارة' in n: return 'stroller'
    elif 'لعب' in n or 'أنشطة' in n or 'مهارات' in n or 'هزازات' in n: return 'toys'
    elif 'نوم' in n or 'بطانيات' in n or 'سرير' in n or 'وسائد' in n: return 'bed'
    elif 'نظافة' in n or 'حفاض' in n or 'مناديل' in n: return 'wash'
    else: return 'checkroom'

def parse_tree_dynamic(lines_text):
    gen = []
    level_counters = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    level_ids = {0: "12"}
    
    for line in lines_text.strip().split('\n'):
        if not line.strip() or line.strip() == '│': continue
        
        match = re.match(r'^[├└│\s─]+', line)
        if not match: continue
        prefix = match.group(0)
        
        name = clean_name(line)
        if not name: continue
        
        # Determine depth dynamically
        # Let's count characters realistically: "├── " is length 4
        # "│   ├── " is length 8
        # "│   │   ├── " is length 12
        # So depth index = len(prefix) // 4
        depth = len(prefix) // 4
        if depth not in level_counters:
            depth = 1 # Fallback just in case
            
        icon = get_icon(name)
        
        level_counters[depth] += 1
        # reset all deeper levels
        for d in range(depth + 1, 6):
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
    '    # FASHION AND BABY (parent=12)',
    '    # ═══════════════════════════════════════════════',
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        break
    
    if '# FASHION AND BABY (parent=' in line:
        skip = True
        
    if skip:
        continue
        
    # Overwrite the parent definition if it is 12
    if '(12, None, "أزياء وجمال"' in line or '(12,  None, "أزياء وجمال"' in line:
        line = '    (12, None, "عالم الموضه ، الجمال، ومستلزمات الطفل", "المكياج، العطور، الأزياء الرجالية والنسائية، ومستلزمات الأطفال", "checkroom", "#E91E63", None, {"en": ["Fashion, Beauty & Baby"]}),\n'
        
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

print(f"Total Fashion categories parsed: {len(generated) - 3}")

# Delete old category 12 root in db if name differs, and children
from database import SessionLocal
from models import Category
db = SessionLocal()

old_kids = db.query(Category).filter(Category.id >= 1200, Category.id < 130000000).all()
for c in old_kids: db.delete(c)
db.commit()

root_cat = db.query(Category).filter_by(id=12).first()
if root_cat:
    root_cat.name = "عالم الموضه ، الجمال، ومستلزمات الطفل"
    db.commit()
db.close()

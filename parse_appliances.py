import re

tree_text = """
├── أدوات ومستلزمات تنظيف
│   ├── مكنسة كهرباء
│   ├── مكنسة روبوت
│   ├── جهاز تنظيف بالبخار
│   ├── ممسحة كهرباء
│   ├── قطع غيار مكانس
│   ├── أدوات تنظيف
│   ├── مواد تنظيف
│   ├── أخرى
├── أجهزة تكييف وتدفئة
│   ├── مكيف
│   ├── مروحة
│   ├── منقّي هواء
│   ├── جهاز ترطيب
│   ├── سخان ماء
│   ├── سخان ماء شمسي
│   ├── رديتر
│   ├── مدفأة كهرباء
│   ├── مدفأة غاز
│   ├── مدفأة كاز
│   ├── ملحقات تكييف وتدفئة
│   ├── أخرى
├── أجهزة مطبخ صغيرة
│   ├── قلاية
│   ├── قلاية هوائية
│   ├── خلاط
│   ├── خلاط عجن
│   ├── محضرة طعام
│   ├── ماكينة قهوة
│   ├── مطحنة قهوة
│   ├── غلاية ماء
│   ├── ميكروويف
│   ├── محمصة خبز
│   ├── شواية كهرباء
│   ├── صانعة ساندويتش
│   ├── صانعة وافل
│   ├── صانعة بان كيك
│   ├── صانعة زبادي
│   ├── صانعة فشار
│   ├── صانعة خبز
│   ├── عصارة
│   ├── مطحنة لحم
│   ├── مبرد ماء
│   ├── فلتر ماء
│   ├── جهاز تفريغ هواء وحفظ الطعام
│   ├── أجهزة طبخ صغيرة أخرى
├── أجهزة مطبخ كبيرة
│   ├── ثلاجة
│   ├── فريزر
│   ├── فرن
│   ├── شفاط مطبخ
│   ├── غسالة صحون
│   ├── طباخ كهرباء
│   ├── أجهزة مطبخ كبيرة أخرى
├── أجهزة عناية بالملابس
│   ├── غسالة ملابس
│   ├── نشافة
│   ├── مكواة
│   ├── جهاز بخار
│   ├── طاولة كوي
│   ├── ماكينة خياطة
│   ├── أدوات وإكسسوارات تفصيل
│   ├── سلة غسيل
│   ├── أجهزة عناية بالملابس أخرى
├── أخرى
"""

lines = tree_text.strip().split('\n')
generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — أجهزة كهربائية منزلية (parent=503)',
    '    # ═══════════════════════════════════════════════',
]

def get_icon(name):
    n = name.lower()
    if 'تنظيف' in n or 'مكنسة' in n or 'ممسحة' in n: return 'cleaning_services'
    elif 'تكييف' in n or 'مكيف' in n or 'مروحة' in n: return 'ac_unit'
    elif 'تدفئة' in n or 'سخان' in n or 'مدفأة' in n or 'رديتر' in n: return 'local_fire_department'
    elif 'مطبخ' in n or 'قلاية' in n or 'خلاط' in n or 'قهوة' in n or 'طعام' in n or 'فرن' in n or 'شواية' in n: return 'kitchen'
    elif 'ثلاجة' in n or 'فريزر' in n or 'مبرد' in n or 'فلتر' in n: return 'kitchen'
    elif 'ملابس' in n or 'غسالة' in n or 'نشافة' in n or 'مكواة' in n or 'خياطة' in n: return 'local_laundry_service'
    else: return 'home'

l1_idx = 0
l2_idx = 0
current_l1_id = None

for line in lines:
    if line.startswith('├──'):
        # Level 1
        l1_idx += 1
        name = line.replace('├──', '').strip()
        icon = get_icon(name)
        current_l1_id = int(f"503{l1_idx:02d}")
        generated.append(f'    ({current_l1_id}, 503, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
        l2_idx = 0
    elif line.startswith('│   ├──'):
        # Level 2
        l2_idx += 1
        name = line.replace('│   ├──', '').strip()
        icon = get_icon(name)
        l2_id = int(f"{current_l1_id}{l2_idx:02d}")
        generated.append(f'    ({l2_id}, {current_l1_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')

generated.append('')

print("Total generated:", len(generated))

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
new_content = re.sub(r'\]\n(\s*)\n\s*def seed\(\):', '\n'.join(generated) + r'\n]\n\n\ndef seed():', content, flags=re.MULTILINE)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated seed_categories.py")

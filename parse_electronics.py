import re

tree_text = """
├── شاشات وبروجكتور وإكسسوارات
│   ├── شاشة
│   ├── شاشة تلفزيون
│   ├── شاشة كمبيوتر
│   ├── شاشة عرض
│   ├── شاشة سيارة
│   ├── شاشة مكسورة
│   ├── بروجكتور
│   ├── شاشة بروجكتور
│   ├── حامل شاشة
│   ├── قاعدة شاشة
│   ├── ريموت
│   ├── كابل شاشة
│   ├── قطعة غيار
│   ├── أخرى
├── كاميرات وإكسسوارات
│   ├── كاميرا
│   ├── كاميرا تصوير
│   ├── كاميرا مراقبة
│   ├── كاميرا فيديو
│   ├── كاميرا سيارة
│   ├── عدسة
│   ├── فلاش
│   ├── حامل كاميرا
│   ├── بطارية كاميرا
│   ├── شاحن كاميرا
│   ├── ذاكرة كاميرا
│   ├── قطعة غيار
│   ├── أخرى
├── أنظمة المنزل الذكية والأمان
│   ├── جهاز ذكي
│   ├── إنذار
│   ├── كاميرا مراقبة
│   ├── جرس باب
│   ├── قفل ذكي
│   ├── حساس
│   ├── جهاز تتبع
│   ├── إضاءة ذكية
│   ├── جهاز تحكم
│   ├── أخرى
├── معدات مكافحة الحشرات
│   ├── جهاز مكافحة حشرات
│   ├── جهاز طارد حشرات
│   ├── جهاز صاعق
│   ├── شبك
│   ├── مصيدة
│   ├── مواد مكافحة
│   ├── أخرى
├── أجهزة صوت وسماعات
│   ├── سماعة
│   ├── سماعة بلوتوث
│   ├── سماعة رأس
│   ├── مكبر صوت
│   ├── مسجل صوت
│   ├── ميكروفون
│   ├── جهاز صوت
│   ├── سماعة سيارة
│   ├── إكسسوارات صوت
│   ├── أخرى
├── عناية شخصية وتصفيف الشعر
│   ├── سشوار
│   ├── مكواة شعر
│   ├── ماكينة حلاقة
│   ├── ماكينة تشذيب
│   ├── فرشاة شعر
│   ├── جهاز بخار شعر
│   ├── جهاز عناية بالبشرة
│   ├── جهاز إزالة شعر
│   ├── جهاز مساج
│   ├── أخرى
├── كابلات شحن ووصلات
│   ├── كابل شحن
│   ├── وصلة
│   ├── محول
│   ├── شاحن
│   ├── شاحن سيارة
│   ├── شاحن لاسلكي
│   ├── وصلة طاقة
│   ├── كابل صوت
│   ├── كابل شاشة
│   ├── كابل بيانات
│   ├── أخرى
├── أخرى
"""

lines = tree_text.strip().split('\n')
generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — إلكترونيات (parent=504)',
    '    # ═══════════════════════════════════════════════',
]

def get_icon(name):
    n = name.lower()
    if 'كاميرا' in n or 'تصوير' in n or 'فيديو' in n or 'عدسة' in n or 'فلاش' in n: return 'camera_alt'
    elif 'صوت' in n or 'سماعة' in n or 'رأس' in n or 'ميكروفون' in n or 'بلوتوث' in n: return 'headphones'
    elif 'شحن' in n or 'كابل' in n or 'طاقة' in n or 'محول' in n or 'بطارية' in n: return 'power'
    elif 'أمان' in n or 'إنذار' in n or 'قفل' in n or 'جرس' in n or 'تتبع' in n: return 'security'
    elif 'شاشة' in n or 'تلفزيون' in n or 'عرض' in n or 'بروجكتور' in n: return 'tv'
    elif 'عناية' in n or 'شعر' in n or 'حلاقة' in n or 'سشوار' in n or 'بشرة' in n: return 'face'
    elif 'حشرات' in n or 'طارد' in n or 'صاعق' in n or 'مكافحة' in n: return 'bug_report'
    elif 'ذكي' in n or 'إضاءة' in n: return 'smart_toy'
    else: return 'devices_other'

l1_idx = 0
l2_idx = 0
current_l1_id = None

for line in lines:
    if line.startswith('├──'):
        # Level 1
        l1_idx += 1
        name = line.replace('├──', '').strip()
        icon = get_icon(name)
        current_l1_id = int(f"504{l1_idx:02d}")
        generated.append(f'    ({current_l1_id}, 504, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
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

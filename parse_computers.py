import re

tree_text = """
├── أجهزة لابتوب
│   ├── لابتوب عادي
│   ├── لابتوب ألعاب Gaming
│   ├── لابتوب أعمال
│   ├── لابتوب خفيف Ultrabook
│   ├── لابتوب مستعمل
│   ├── أخرى
├── أجهزة كمبيوتر مكتبية
│   ├── كمبيوتر مكتبي عادي
│   ├── كمبيوتر ألعاب Gaming PC
│   ├── كمبيوتر تصميم ومونتاج
│   ├── كمبيوتر شركات
│   ├── أخرى
├── أجهزة الكل في واحد All-in-One
│   ├── All in One HP
│   ├── All in One Dell
│   ├── All in One Lenovo
│   ├── أخرى
├── شاشات كمبيوتر
│   ├── شاشات عادية
│   ├── شاشات Gaming
│   ├── شاشات 4K
│   ├── شاشات Ultrawide
│   ├── أخرى
├── خوادم Servers
│   ├── Rack Server
│   ├── Tower Server
│   ├── Blade Server
│   ├── Server Parts
│   ├── أخرى
├── قطع الهاردوير
│   ├── معالجات CPU
│   ├── كروت شاشة GPU
│   ├── رامات RAM
│   ├── لوحات أم Motherboard
│   ├── مزود طاقة PSU
│   ├── صناديق كمبيوتر Case
│   ├── مراوح تبريد
│   ├── تبريد مائي
│   ├── كروت صوت
│   ├── كروت شبكة
│   ├── أخرى
├── وحدات التخزين
│   ├── HDD
│   ├── SSD
│   ├── NVMe
│   ├── هارد خارجي
│   ├── فلاش USB
│   ├── كرت ذاكرة
│   ├── NAS
│   ├── أخرى
├── إكسسوارات كمبيوتر
│   ├── كيبورد
│   ├── ماوس
│   ├── ماوس باد
│   ├── سماعات
│   ├── ميكروفون
│   ├── كاميرا ويب
│   ├── قواعد لابتوب
│   ├── حقائب لابتوب
│   ├── إضاءة RGB
│   ├── أخرى
├── طابعات وماكينات تصوير
│   ├── طابعات ليزر
│   ├── طابعات حبر
│   ├── طابعات حرارية
│   ├── ماكينات تصوير
│   ├── طابعات ثلاثية الأبعاد
│   ├── أخرى
├── أحبار وإكسسوارات طابعات
│   ├── أحبار
│   ├── تونر
│   ├── رؤوس طباعة
│   ├── ورق طباعة
│   ├── أخرى
├── حلول الشبكات والربط
│   ├── راوتر
│   ├── مودم
│   ├── سويتش
│   ├── Access Point
│   ├── كروت شبكة
│   ├── مقويات إشارة
│   ├── كابلات شبكة
│   ├── Rack
│   ├── أخرى
├── برامج وأنظمة تشغيل
│   ├── Windows
│   ├── MacOS
│   ├── Linux
│   ├── Office
│   ├── برامج تصميم
│   ├── برامج حماية
│   ├── برامج محاسبة
│   ├── أخرى
├── ماسحات ضوئية
│   ├── Scanner عادي
│   ├── Scanner احترافي
│   ├── Barcode Scanner
│   ├── Document Scanner
│   ├── أخرى
├── كابلات ومحولات
│   ├── HDMI
│   ├── VGA
│   ├── DisplayPort
│   ├── USB
│   ├── Type-C
│   ├── LAN
│   ├── محولات كهرباء
│   ├── Docking Station
│   ├── أخرى
├── أجهزة عرض Projectors
│   ├── بروجكتر منزلي
│   ├── بروجكتر تعليمي
│   ├── بروجكتر احترافي
│   ├── شاشات عرض
│   ├── أخرى
├── أخرى
"""

lines = tree_text.strip().split('\n')
generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — لابتوب وكمبيوتر (parent=501)',
    '    # ═══════════════════════════════════════════════'
]

# We map known icons by searching for keywords
def get_icon(name):
    n = name.lower()
    if 'لابتوب' in n: return 'laptop_mac'
    elif 'شاشات' in n or 'display' in n or 'vga' in n or 'hdmi' in n: return 'monitor'
    elif 'خوادم' in n or 'server' in n or 'شبكات' in n or 'راوتر' in n: return 'dns'
    elif 'تخزين' in n or 'هارد' in n or 'ssd' in n or 'hdd' in n: return 'storage'
    elif 'طابعات' in n or 'تصوير' in n or 'أحبار' in n: return 'print'
    elif 'إكسسوارات' in n or 'كيبورد' in n or 'ماوس' in n: return 'mouse'
    elif 'برامج' in n or 'أنظمة' in n or 'windows' in n: return 'code'
    elif 'ماسحات' in n or 'scanner' in n: return 'scanner'
    elif 'عرض' in n or 'projector' in n: return 'videocam'
    elif 'هاردوير' in n or 'معالج' in n or 'رامات' in n or 'كروت' in n: return 'memory'
    elif 'كابلات' in n or 'محولات' in n or 'usb' in n: return 'cable'
    else: return 'computer'

l1_idx = 0
l2_idx = 0
current_l1_id = None

for line in lines:
    if line.startswith('├──'):
        # Level 1
        l1_idx += 1
        name = line.replace('├──', '').strip()
        icon = get_icon(name)
        current_l1_id = int(f"501{l1_idx:02d}")
        generated.append(f'    ({current_l1_id}, 501, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
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

# I will find the block previously generated that contains the 901 definitions, and remove it.
# It starts around '# SECOND-LEVEL — لابتوب وكمبيوتر (parent=501)' and ends before '# SECOND-LEVEL — شاشات ورسيفرات (parent=502)'
import re
new_content = re.sub(r'    # ═══════════════════════════════════════════════\n    # SECOND-LEVEL — لابتوب وكمبيوتر \(parent=501\).*?(?=    # ═══════════════════════════════════════════════\n    # SECOND-LEVEL — شاشات ورسيفرات \(parent=502\))', '\n'.join(generated) + '\n', content, flags=re.DOTALL)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated seed_categories.py")

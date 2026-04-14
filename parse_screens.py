import re

tree_text = """
├── شاشات
│   ├── شاشة تلفزيون
│   ├── شاشة كمبيوتر
│   ├── شاشة عرض
│   ├── شاشة سيارة
│   ├── شاشة مكسورة
│   ├── شاشة مع قطع
│   ├── أخرى
├── رسيفرات
│   ├── رسيفر
│   ├── رسيفر فضائي
│   ├── رسيفر عادي
│   ├── رسيفر ذكي
│   ├── رسيفر مكسور
│   ├── رسيفر مع قطع
│   ├── أخرى
├── ملحقات شاشات ورسيفرات
│   ├── ريموت
│   ├── حامل شاشة
│   ├── قاعدة شاشة
│   ├── كيبلات
│   ├── وصلات
│   ├── قطع غيار
│   ├── أخرى
├── أجهزة عرض
│   ├── بروجكتر
│   ├── شاشة بروجكتر
│   ├── ملحقات بروجكتر
│   ├── أخرى
├── أخرى
"""

lines = tree_text.strip().split('\n')
generated = [
    '    # ═══════════════════════════════════════════════',
    '    # SECOND-LEVEL — شاشات ورسيفرات (parent=502)',
    '    # ═══════════════════════════════════════════════',
]

def get_icon(name):
    n = name.lower()
    if 'تلفزيون' in n or 'شاشة' in n or 'شاشات' in n: return 'tv'
    elif 'رسيفر' in n: return 'router'
    elif 'بروجكتر' in n or 'أجهزة عرض' in n: return 'videocam'
    elif 'ريموت' in n or 'ملحقات' in n or 'حامل' in n or 'كيبلات' in n: return 'settings_remote'
    else: return 'tv'

l1_idx = 0
l2_idx = 0
current_l1_id = None

for line in lines:
    if line.startswith('├──'):
        # Level 1
        l1_idx += 1
        name = line.replace('├──', '').strip()
        icon = get_icon(name)
        current_l1_id = int(f"502{l1_idx:02d}")
        generated.append(f'    ({current_l1_id}, 502, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
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

# I will find the end of the `CATEGORIES = [` array (which ends with `]`)
# and inject my generated categories right before the closing bracket.
import re
new_content = re.sub(r'\]\n(\s*)\n\s*def seed\(\):', '\n'.join(generated) + r'\n]\n\n\ndef seed():', content, flags=re.MULTILINE)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated seed_categories.py")

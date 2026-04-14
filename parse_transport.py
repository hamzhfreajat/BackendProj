import re

tree_text = """
├── مشاركة ركوب
│   ├── رحلة مشتركة
│   ├── مشوار مشترك
│   ├── توصيل يومي
│   ├── ذهاب إلى العمل
│   ├── ذهاب إلى الجامعة
│   ├── بين المدن
│   ├── من وإلى المطار
│   ├── أخرى

├── سيارات أجرة وخدمة نقل
│   ├── تاكسي
│   ├── سائق خاص
│   ├── سيارة مع سائق
│   ├── خدمة نقل
│   ├── مشاوير خاصة
│   ├── أخرى

├── باصات وفانات
│   ├── باص
│   ├── ميني باص
│   ├── فان
│   ├── نقل جماعي
│   ├── نقل موظفين
│   ├── نقل مدارس
│   ├── رحلات
│   ├── أخرى

├── تنقل بين المدن
│   ├── نقل يومي
│   ├── سفر بين المحافظات
│   ├── مشاوير بعيدة
│   ├── أخرى

├── خدمات توصيل الركاب
│   ├── توصيل مشاوير
│   ├── توصيل مطار
│   ├── توصيل فعاليات
│   ├── توصيل مناسبات
│   ├── أخرى

└── أخرى
"""

def clean_name(name):
    # Remove tree drawing lines
    name = re.sub(r'^[├└│\s─]+', '', name)
    return name.strip()

def get_icon(name):
    n = name.lower()
    if 'مطار' in n: return 'flight_takeoff'
    elif 'باص' in n or 'جماعي' in n or 'فان' in n or 'نقل' in n or 'مدارس' in n: return 'directions_bus'
    elif 'تاكسي' in n or 'أجرة' in n: return 'local_taxi'
    elif 'جامع' in n or 'عمل' in n: return 'commute'
    elif 'سائق' in n: return 'person'
    elif 'مشترك' in n or 'مشاركة' in n: return 'group'
    elif 'مدن' in n or 'محافظات' in n: return 'location_city'
    elif 'رحلة' in n or 'سفر' in n or 'مشاوير' in n or 'توصيل' in n: return 'route'
    else: return 'directions_car'

def parse_tree(lines_text):
    gen = []
    l1_idx = 0
    l2_idx = 0
    current_l1_id = None
    
    for line in lines_text.strip().split('\\n'):
        if not line.strip(): continue
        
        match = re.match(r'^[├└│\s─]+', line)
        if not match: continue
        prefix = match.group(0)
        
        name = clean_name(line)
        icon = get_icon(name)
        depth = len(prefix)
        
        # Level 1 usually starts directly with ├── or └── (len ~4)
        if depth < 6:
            l1_idx += 1
            current_l1_id = int(f"9{l1_idx:02d}")
            gen.append(f'    ({current_l1_id}, 9, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')
            l2_idx = 0
            
        # Level 2 usually starts with │   ├── or └── (len ~8)
        else:
            l2_idx += 1
            l2_id = int(f"{current_l1_id}{l2_idx:02d}")
            gen.append(f'    ({l2_id}, {current_l1_id}, "{name}", None, "{icon}", None, None, {{"en": ["{name}"]}}),')

    return gen

gen_list = parse_tree(tree_text)

generated = [
    '    # ═══════════════════════════════════════════════',
    '    # TRANSPORTATION AND RIDESHARING (parent=9)',
    '    # ═══════════════════════════════════════════════',
] + gen_list

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
skip = False
for line in lines:
    if line.strip() == ']':
        break
    
    # Let's skip any previous injects just in case
    if '# TRANSPORTATION AND RIDESHARING (parent=9)' in line:
        skip = True
        
    if skip:
        continue
        
    out_lines.append(line)

for gl in generated:
    out_lines.append(gl + '\\n')

out_lines.append(']\\n\\n\\n')

# Append the seed function correctly
seed_started = False
for line in lines:
    if line.startswith('def seed():'):
        seed_started = True
    
    if seed_started:
        out_lines.append(line)

# Make sure we don't write double backslashes
with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(''.join(out_lines).replace('\\n', '\\n').replace('\\n\\n', '\\n\\n'))  # Handle literal backslashes from our string above
    pass # Wait! We generated the strings with literally '\\n' above. Let me use '\n' in the script directly instead!


import re

tree_text = """
├── 🛋️ الأثاث والديكور الداخلي
│   ├── أثاث غرف المعيشة
│   │   ├── طقم كنب
│   │   └── أخرى
│   └── الديكور وإكسسوارات المنزل
│       ├── مرآة
│       └── أخرى
├── 🍳 المطبخ وغرف السفرة
│   ├── أثاث غرف السفرة
│   │   ├── طاولة طعام
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    name = re.sub(r'^[^\\w\\u0600-\\u06FF]+', '', name)
    return name.strip()

def parse_tree(lines_text, parent_id, prefix):
    lines = lines_text.strip().split('\\n')
    gen = []
    l1_idx = 0; l2_idx = 0; l3_idx = 0
    current_l1_id = None
    current_l2_id = None
    
    for line in lines:
        if not line.strip(): continue
        
        if line.startswith('├── ') or line.startswith('└── '):
            l1_idx += 1
            name = clean_name(line)
            current_l1_id = int(f"{prefix}{l1_idx:02d}")
            gen.append(f'L1: ({current_l1_id}, {parent_id}, "{name}")')
            l2_idx = 0; l3_idx = 0
            
        elif line.startswith('│   ├──') or line.startswith('│   └──') or line.startswith('    ├──') or line.startswith('    └──'):
            l2_idx += 1
            name = clean_name(line)
            current_l2_id = int(f"{current_l1_id}{l2_idx:02d}")
            gen.append(f'L2: ({current_l2_id}, {current_l1_id}, "{name}")')
            l3_idx = 0
            
        elif '│   │   ├──' in line or '│   │   └──' in line or '        ├──' in line or '        └──' in line or '│       ├──' in line or '│       └──' in line:
            l3_idx += 1
            name = clean_name(line)
            l3_id = int(f"{current_l2_id}{l3_idx:02d}")
            gen.append(f'L3: ({l3_id}, {current_l2_id}, "{name}")')

    return gen

for g in parse_tree(tree_text, 7, "7"):
    print(g)

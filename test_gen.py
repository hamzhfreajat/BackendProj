import re

tree_text = """
├── 🐕 كلاب
│   ├── كلاب للبيع
│   │   ├── كلاب حراسة
"""

def clean_name(name):
    name = re.sub(r'^[├└│\s─]+', '', name)
    return "".join(c for c in name if c.isalnum() or c.isspace() or c in "/-.").strip()

gen = []
l1_idx = 0; l2_idx = 0; l3_idx = 0
current_l1_id = None; current_l2_id = None

for line in tree_text.strip().split('\n'):
    if not line.strip(): continue
    
    match = re.match(r'^[├└│\s─]+', line)
    if not match: continue
    prefix = match.group(0)
    
    name = clean_name(line)
    depth = len(prefix)
    
    if depth < 6:
        l1_idx += 1
        current_l1_id = int(f"10{l1_idx:02d}")
        gen.append(f'L1: {current_l1_id} - {name} (depth={depth})')
        l2_idx = 0; l3_idx = 0
    elif depth < 10:
        l2_idx += 1
        current_l2_id = int(f"{current_l1_id}{l2_idx:02d}")
        gen.append(f'L2: {current_l2_id} - {name} (depth={depth})')
        l3_idx = 0
    else:
        l3_idx += 1
        l3_id = int(f"{current_l2_id}{l3_idx:02d}")
        gen.append(f'L3: {l3_id} - {name} (depth={depth})')

for g in gen: print(g)


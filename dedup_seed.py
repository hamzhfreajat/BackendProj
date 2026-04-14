import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
seen_ids = set()
in_list = False

for line in lines:
    if line.startswith('CATEGORIES = ['):
        in_list = True
        out.append(line)
        continue
    
    if in_list and line.strip() == ']':
        in_list = False
        out.append(line)
        continue
        
    if in_list:
        match = re.match(r'^\s*\((\d+),', line)
        if match:
            cid = int(match.group(1))
            if cid in seen_ids:
                # Duplicate! Skip it
                continue
            seen_ids.add(cid)
    
    out.append(line)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print(len(seen_ids), "unique categories kept!")

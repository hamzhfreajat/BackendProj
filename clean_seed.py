import json
import re

with open('temp_redundants.json', encoding='utf-8') as f:
    res = json.load(f)

del_ids = {str(r['id']) for r in res}

with open('seed_categories.py', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
skip = False

for line in lines:
    stripped = line.strip()
    
    # Check if this line starts a new tuple like `(3011,` and if the ID is in our deletion list
    match = re.search(r'^\((\d+),', stripped)
    if match:
        cat_id = match.group(1)
        if cat_id in del_ids:
            skip = True
            continue
            
    # If we are skipping, we look for the end of the tuple `}),`
    if skip:
        if stripped.endswith('}),'):
            skip = False
        continue
        
    new_lines.append(line)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
    
print(f"Purged {len(del_ids)} items from seed_categories.py")

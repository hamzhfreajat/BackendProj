import json
with open('cats.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find descendants of 3, 2, 10313
roots = {3, 2, 10313}
root_names = {c['id']: c['name'] for c in data if c['id'] in roots}

with open('cats_out.txt', 'w', encoding='utf-8') as f:
    f.write('Roots: ' + json.dumps(root_names, ensure_ascii=False) + '\n')
    for root_id in roots:
        f.write(f'\nChildren of {root_names.get(root_id)} ({root_id}):\n')
        children = [c for c in data if c['parent_id'] == root_id]
        for child in children:
            f.write(f"  - {child['name']} ({child['id']})\n")

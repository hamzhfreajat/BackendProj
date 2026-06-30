import json
import sys

with open('all_categories_dump.json', 'r', encoding='utf-8') as f:
    cats = json.load(f)

tree = {}
for c in cats:
    tree[c['id']] = c

output_lines = []
def print_tree(node_id, level=0):
    node = tree[node_id]
    output_lines.append('  ' * level + f"- {node['id']}: {node['name']}")
    for c in cats:
        if c['parent_id'] == node_id:
            print_tree(c['id'], level + 1)

real_estate_roots = [2, 3] # 2 is sale, 3 is rent
for r in real_estate_roots:
    if r in tree:
        print_tree(r)

with open('tree_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

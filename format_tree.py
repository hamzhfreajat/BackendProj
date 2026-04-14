import json
import collections

with open('temp_tree.json', encoding='utf-8') as f:
    cats = json.load(f)

# Build a dictionary to map category IDs to their children
children_map = collections.defaultdict(list)
root_cats = []

# Sort categories to ensure consistent ordering based on ID
cats = sorted(cats, key=lambda x: x['id'])

for c in cats:
    if not c['parent_id']:
        root_cats.append(c)
    else:
        children_map[c['parent_id']].append(c)

def print_tree(node, prefix="", is_last=True, is_root=False):
    # Determine the prefix symbols
    if is_root:
        marker = "■"
    else:
        marker = "└──" if is_last else "├──"

    output = f"{prefix}{marker} {node['name']} (ID: {node['id']})\n"
    
    # Calculate prefix for children
    if not is_root:
        child_prefix = prefix + ("    " if is_last else "│   ")
    else:
        child_prefix = "   "

    children = children_map[node['id']]
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        output += print_tree(child, child_prefix, is_last=is_last_child)
        
    return output

# Form markdown file
full_md = "# Full Application Category Tree\n\n"
full_md += "Here is the exact state of all categories in the active database, accounting for the deduplication you requested earlier. \n\n"
full_md += "```text\n"
for root in root_cats:
    full_md += print_tree(root, is_root=True)
    full_md += "\n"
full_md += "```\n"

with open('category_tree.md', 'w', encoding='utf-8') as f:
    f.write(full_md)

print("Generated category tree markdown.")

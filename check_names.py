import json
with open('cats.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('check_names.txt', 'w', encoding='utf-8') as out:
    for c in data:
        if 'شقق' in c['name'] or 'ستوديوهات' in c['name'] or 'ملحق' in c['name'] or 'دوبلكس' in c['name']:
            out.write(f"{c['name']} ({c['id']}) - Parent: {c['parent_id']}\n")

import json
with open('cats.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('cats2_out.txt', 'w', encoding='utf-8') as out:
    for pid in [310, 10310]:
        out.write(f'\nChildren of {pid}:\n')
        for c in data:
            if c['parent_id'] == pid:
                out.write(f"  - {c['name']} ({c['id']})\n")

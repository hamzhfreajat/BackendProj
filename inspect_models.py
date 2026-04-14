import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('os_models.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

values = data['result']['data']['values']
print(f'Total elements fetched: {len(values)}')

brands = set()
for v in values:
    # "options" has what?
    if 'parent_value' in v:
         brands.add(v['parent_value'])

print("Sample elements:")
for v in values[:3]:
    print(v)

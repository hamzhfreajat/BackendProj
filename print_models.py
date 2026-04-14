import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('os_models.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

values = data.get('data', {}).get('values', [])
print(f'Total brands fetched: {len(values)}')

for v in values[:3]:
    print(f"Brand: {v.get('label')}, ID: {v.get('id')}")
    options = v.get('options', [])
    print(f"  Models: {len(options)}")
    for opt in options[:3]:
        print(f"    - {opt.get('label')}")

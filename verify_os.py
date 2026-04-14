import json
import psycopg
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read Brands
with open('os_brands.json', 'r', encoding='utf-8') as f:
    b_data = json.load(f)
brands = b_data['result']['data']['values']

# Read Models
with open('os_models.json', 'r', encoding='utf-8') as f:
    m_data = json.load(f)
models_list = m_data['result']['data']['values']

# Map Models to Brands
models_by_brand_val = {}
for m in models_list:
    pv = m.get('parent_value')
    if pv not in models_by_brand_val:
        models_by_brand_val[pv] = []
    models_by_brand_val[pv].append(m)

print(f"Loaded {len(brands)} brands and {len(models_list)} models total.")

total_models_mapped = sum([len(v) for v in models_by_brand_val.values()])
print(f"Models mapped to a parent: {total_models_mapped}")

# Show mappings
for b in brands[:3]:
    b_val = b['value']
    print(f"\nBrand: {b['label']} (value/id: {b_val})")
    child_models = models_by_brand_val.get(b_val, [])
    for cm in child_models:
        print(f"   - Model: {cm['label']} (id: {cm['id']})")

import json
import psycopg
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('os_brands.json', 'r', encoding='utf-8') as f:
    brands_data = json.load(f)
brands = brands_data['result']['data']['values']

with open('os_models.json', 'r', encoding='utf-8') as f:
    models_data = json.load(f)
models_list = models_data['result']['data']['values']

models_by_brand = {}
for m in models_list:
    pv = m.get('parent_value')
    if pv not in models_by_brand:
        models_by_brand[pv] = []
    models_by_brand[pv].append(m)

types_ids = list(range(103101, 103116)) # 103101 to 103115

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# 1. Delete AI Models
print("Deleting old AI generated models...")
cur.execute('DELETE FROM categories WHERE id >= 10310100 AND id < 10320000')
print(f"Deleted {cur.rowcount} rows.")

# 2. Insert OS Models
current_id = 10310100
total_inserted = 0

for t_id in types_ids:
    for b in brands:
        # Check if this brand has models (optional: maybe OS returns all brands)
        b_val = b['id'] # The ID in the JSON is string
        b_name = b['label']
        b_icon = b.get('icon')
        
        brand_id = current_id
        current_id += 1
        
        # Insert Brand under 't_id'
        cur.execute(
            'INSERT INTO categories (id, parent_id, name, icon_name, order_index) VALUES (%s, %s, %s, %s, 0)',
            (brand_id, t_id, b_name, b_icon)
        )
        total_inserted += 1
        
        # Insert Models under Brand
        child_models = models_by_brand.get(b_val, [])
        for m in child_models:
            m_name = m['label']
            m_icon = m.get('icon')
            
            model_id = current_id
            current_id += 1
            cur.execute(
                'INSERT INTO categories (id, parent_id, name, icon_name, order_index) VALUES (%s, %s, %s, %s, 0)',
                (model_id, brand_id, m_name, m_icon)
            )
            total_inserted += 1

conn.commit()
print(f"Successfully inserted {total_inserted} true OS categories!")
conn.close()

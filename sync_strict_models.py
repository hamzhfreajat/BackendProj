import json
import psycopg
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read Brands (48)
with open('os_brands.json', 'r', encoding='utf-8') as f:
    brands_data = json.load(f)
brands = brands_data['result']['data']['values']

# Read Models (77 - the Yamaha ones retrieved by user's API URL)
with open('os_models.json', 'r', encoding='utf-8') as f:
    models_data = json.load(f)
models_list = models_data['result']['data']['values']

types_ids = list(range(103101, 103116)) # 103101 to 103115

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# 1. Wipe AI Models completely
print("Deleting all AI generated categories for motorbikes (and cascading)...")
cur.execute('DELETE FROM categories WHERE id >= 10310100 AND id < 10500000')
print(f"Deleted {cur.rowcount} orphan categories.")

# 2. Insert OS Brands and Models
current_id = 10310100
total_brands_inserted = 0
total_models_inserted = 0

for t_id in types_ids:
    for b in brands:
        b_val = b['id'] # OS Brand ID string, e.g. "4563" for Yamaha
        b_name = b['label']
        b_icon = b.get('icon')
        
        brand_id = current_id
        current_id += 1
        
        cur.execute(
            'INSERT INTO categories (id, parent_id, name, icon_name, order_index) VALUES (%s, %s, %s, %s, 0)',
            (brand_id, t_id, b_name, b_icon)
        )
        total_brands_inserted += 1
        
        # Since the user's API payload only returned Yamaha models (77 rows), 
        # we strictly only attach them to Yamaha ("4563") to avoid 50,000 false permutations.
        if b_val == "4563":
            for m in models_list:
                m_name = m['label']
                m_icon = m.get('icon')
                
                model_id = current_id
                current_id += 1
                cur.execute(
                    'INSERT INTO categories (id, parent_id, name, icon_name, order_index) VALUES (%s, %s, %s, %s, 0)',
                    (model_id, brand_id, m_name, m_icon)
                )
                total_models_inserted += 1

conn.commit()
print(f"Successfully inserted {total_brands_inserted} real OS Brands!")
print(f"Successfully inserted {total_models_inserted} real OS Models (attached strictly to Yamaha)!")
conn.close()

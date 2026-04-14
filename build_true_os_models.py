import requests
import json
import psycopg
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. Fetch exact 48 BRANDS from API
url_brands = 'https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpMake_Motorbike&type=add-post&workflowId=425350&draftId=d94c8dae-f52f-48e2-9b95-7d0cacd83f51&stepId=post_previewStep&expand=remaining_edit_counter,media,post.overLimitType,post.isOverLimit&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1'
url_models_base = 'https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpMake_Motorbike_child&type=add-post&workflowId=425350&draftId=d94c8dae-f52f-48e2-9b95-7d0cacd83f51&stepId=post_previewStep&expand=remaining_edit_counter,media,post.overLimitType,post.isOverLimit&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1'

headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI2Mzk0MTIiLCJleHAiOjE3NzU0ODUyODl9.EVhbrqh_tprAGUmYCuN6EUghN0FhLcJ2EvISa3ry0WA',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0',
    'Country': 'jo',
    'Source': '1'
}

print("Fetching Brands...")
r_brands = requests.get(url_brands, headers=headers)
brands_list = r_brands.json()['result']['data']['values']
print(f"Fetched {len(brands_list)} exact OS Brands.")

models_by_brand = {}
total_models = 0

print("Fetching Models dynamically per Brand...")
for b in brands_list:
    b_id = b['id']
    r_mod = requests.get(url_models_base + f"&parent_value={b_id}", headers=headers)
    if r_mod.status_code == 200:
        data = r_mod.json()
        if 'result' in data and 'data' in data['result'] and 'values' in data['result']['data']:
            models = data['result']['data']['values']
            models_by_brand[b_id] = models
            total_models += len(models)

print(f"Fetched {total_models} true OS Models across all brands.")

# 2. Database cleanup and insertion
types_ids = list(range(103101, 103116)) # 103101 to 103115
conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

print("Deleting old AI generated models (and cascading)...")
cur.execute('DELETE FROM categories WHERE id >= 10310100 AND id < 10320000')
print(f"Deleted {cur.rowcount} parent brands (and their cascaded children).")

print("Injecting exact OS tree into all 15 Custom types...")
current_id = 10310100
total_inserted = 0

for t_id in types_ids:
    for b in brands_list:
        b_val = b['id']
        b_name = b['label']
        b_icon = b.get('icon')
        
        brand_id = current_id
        current_id += 1
        
        cur.execute(
            'INSERT INTO categories (id, parent_id, name, icon_name, order_index) VALUES (%s, %s, %s, %s, 0)',
            (brand_id, t_id, b_name, b_icon)
        )
        total_inserted += 1
        
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
print(f"Successfully inserted {total_inserted} EXACT OS categories!")
conn.close()

import json
import requests
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'country': 'jo',
    'source': '1',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI4MTIyMzMiLCJleHAiOjE3NzQ0MjUyMjR9.QgR1yL3LVZ21Js7nnKuHN7oiHDVVzlZt7Ojm7tHR1XY'
}

print("Loading brands.json...")
try:
    with open('brands.json', 'r', encoding='utf-8') as f:
        bt_data = json.load(f)
    if 'result' in bt_data and 'data' in bt_data['result']:
        brands_list = bt_data['result']['data']['values']
    else:
        print("Brands list missing from json file, parsing error")
        exit(1)
except Exception as e:
    print(f"Error loading brands: {e}")
    exit(1)

generated_tuples = [
    '    # ═══════════════════════════════════════════════',
    '    # THIRD-LEVEL — موبايلات (parent=410) / Brands and Models',
    '    # ═══════════════════════════════════════════════'
]

print(f"Loaded {len(brands_list)} brands. Fetching models...")

for i, brand in enumerate(brands_list):
    brand_id = int(brand['id'])
    brand_name = brand['label'].replace('"', '\\"')
    generated_tuples.append(f'    ({brand_id}, 410, "{brand_name}", "smartphone", "هواتف {brand_name}", None, None, {{"en": ["{brand_name}"]}}),')

    url = f"https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpPhones_Brand_child&type=add-post&workflowId=401122&draftId=5cc5b3eb-b97c-450f-99af-816cf7d96770&stepId=post_previewStep&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1&cpPhones_Brand={brand_id}"
    
    retries = 3
    models_list = []
    
    while retries > 0:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()
            if 'result' in data and 'data' in data['result']:
                # The sub-brand list might be empty for some brands like "Others"
                vals = data['result']['data'].get('values')
                if vals:
                    models_list = vals
                break
        except Exception as e:
            pass
        retries -= 1
        time.sleep(1)
    
    print(f"[{i+1}/{len(brands_list)}] Brand {brand_name} (ID: {brand_id}) -> {len(models_list)} models")
    
    for model in models_list:
        model_id = int(model['id'])
        model_name = model['label'].replace('"', '\\"')
        generated_tuples.append(f'    ({model_id}, {brand_id}, "{model_name}", "devices_other", "موبايل {model_name}", None, None, {{"en": ["{model_name}"]}}),')
        
    time.sleep(0.3)

generated_tuples.append('')

print(f"Total entries generated: {len(generated_tuples)}")

print("Updating seed_categories.py...")
with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "THIRD-LEVEL — موبايلات (parent=410)" in line and start_idx == -1:
        start_idx = i - 1
    if "THIRD-LEVEL — تابلت (parent=420)" in line and start_idx != -1:
        end_idx = i - 1
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + generated_tuples + lines[end_idx:]
    with open('seed_categories.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("seed_categories.py updated successfully!")
else:
    print(f"Error: Could not find insertion boundaries: start={start_idx}, end={end_idx}")
    with open('categories_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(generated_tuples))

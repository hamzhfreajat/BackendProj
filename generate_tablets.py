import json
import requests
import time

TABLETS_JSON = """
{
    "success": true,
    "result": {
        "status": 200,
        "hash": "0b2905c5068608b1502198e417ae084f",
        "data": {
            "identifier": "cpTablets_Brand",
            "type": "listCellOptions",
            "fullscreen": true,
            "values": [
                {"id": "10224", "label": "HP"},
                {"id": "17608", "label": "XP-PEN"},
                {"id": "10210", "label": "آسوس"},
                {"id": "3977", "label": "أبل"},
                {"id": "10214", "label": "أركوس"},
                {"id": "15106", "label": "ألكاتيل"},
                {"id": "10212", "label": "أمازون"},
                {"id": "10220", "label": "إي نيت"},
                {"id": "3985", "label": "إيسر"},
                {"id": "38447", "label": "اوتيتو"},
                {"id": "39309", "label": "اوسكال"},
                {"id": "38503", "label": "ايتل"},
                {"id": "38483", "label": "ايه تتش"},
                {"id": "38285", "label": "بلاك فيو"},
                {"id": "10216", "label": "بلاكبيري"},
                {"id": "17791", "label": "تاج تيك"},
                {"id": "38249", "label": "تشوي"},
                {"id": "23282", "label": "تكلاست"},
                {"id": "15350", "label": "تكنو"},
                {"id": "10228", "label": "توشيبا"},
                {"id": "38343", "label": "تي سي ال"},
                {"id": "10222", "label": "جوجل"},
                {"id": "17807", "label": "جي تاب"},
                {"id": "38383", "label": "دوجي"},
                {"id": "10218", "label": "ديل"},
                {"id": "3979", "label": "سامسونج"},
                {"id": "3981", "label": "سوني"},
                {"id": "20535", "label": "شاومي"},
                {"id": "38329", "label": "فولج"},
                {"id": "23280", "label": "فيكوشا"},
                {"id": "3987", "label": "لينوفو"},
                {"id": "3983", "label": "مايكروسوفت"},
                {"id": "38373", "label": "موديو"},
                {"id": "38437", "label": "نوكيا"},
                {"id": "10226", "label": "هواوي"},
                {"id": "17751", "label": "هونور"},
                {"id": "17596", "label": "هيون"},
                {"id": "17576", "label": "واكوم"},
                {"id": "38397", "label": "ون بلس"},
                {"id": "3989", "label": "اخرى"}
            ]
        }
    }
}
"""

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'country': 'jo',
    'source': '1',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI4MTIyMzMiLCJleHAiOjE3NzQ0MjUyMjR9.QgR1yL3LVZ21Js7nnKuHN7oiHDVVzlZt7Ojm7tHR1XY'
}

bt_data = json.loads(TABLETS_JSON)
brands_list = bt_data['result']['data']['values']

generated_tuples = [
    '    # ═══════════════════════════════════════════════',
    '    # THIRD-LEVEL — تابلت (parent=420) / Brands and Models',
    '    # ═══════════════════════════════════════════════'
]

print(f"Loaded {len(brands_list)} tablet brands. Fetching models...")

for i, brand in enumerate(brands_list):
    brand_id = int(brand['id'])
    brand_name = brand['label'].replace('"', '\\"')
    generated_tuples.append(f'    ({brand_id}, 420, "{brand_name}", "تابلت {brand_name}", "tablet_mac", None, None, {{"en": ["{brand_name}"]}}),')

    url = f"https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpTablets_Brand_child&type=add-post&workflowId=401126&draftId=5cc5b3eb-b97c-450f-99af-816cf7d96770&stepId=post_previewStep&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1&cpTablets_Brand={brand_id}"
    
    retries = 3
    models_list = []
    
    while retries > 0:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            data = r.json()
            if 'result' in data and 'data' in data['result']:
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
        generated_tuples.append(f'    ({model_id}, {brand_id}, "{model_name}", "تابلت {model_name}", "tablet_mac", None, None, {{"en": ["{model_name}"]}}),')
        
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
    if "THIRD-LEVEL — تابلت (parent=420)" in line and start_idx == -1:
        start_idx = i - 1
    if "THIRD-LEVEL — ساعات ذكية (parent=430)" in line and start_idx != -1:
        end_idx = i - 1
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + generated_tuples + lines[end_idx:]
    with open('seed_categories.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("seed_categories.py updated successfully!")
else:
    print(f"Error: Could not find insertion boundaries: start={start_idx}, end={end_idx}")
    with open('tablets_out.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(generated_tuples))

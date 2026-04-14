import json
import re

WATCHES_JSON = """
{
    "success": true,
    "result": {
        "status": 200,
        "hash": "12989989d51f30e645d7c433a61a1718",
        "data": {
            "identifier": "cpSmartWatchesBrand",
            "type": "listCellOptions",
            "fullscreen": true,
            "values": [
                {"id": "19371", "label": "ابل"},
                {"id": "19381", "label": "اتش تي سي"},
                {"id": "19375", "label": "ال جي"},
                {"id": "38891", "label": "الترا"},
                {"id": "21718", "label": "اميزفيت"},
                {"id": "19383", "label": "اي تاتش"},
                {"id": "38897", "label": "تكنو"},
                {"id": "19387", "label": "تيكووتش"},
                {"id": "38907", "label": "جارمن"},
                {"id": "38903", "label": "جوجل"},
                {"id": "38901", "label": "جويروم"},
                {"id": "38899", "label": "جي تاب"},
                {"id": "38893", "label": "جي تي"},
                {"id": "19379", "label": "سامسونج"},
                {"id": "19385", "label": "سوني"},
                {"id": "38905", "label": "شاومي"},
                {"id": "38895", "label": "فت بت"},
                {"id": "23278", "label": "فيكوشا"},
                {"id": "19377", "label": "موتورولا"},
                {"id": "38911", "label": "موديو"},
                {"id": "38887", "label": "نوثينغ ووتش"},
                {"id": "19373", "label": "هواوي"},
                {"id": "38913", "label": "هونور"},
                {"id": "38889", "label": "ون بلس"},
                {"id": "38909", "label": "يسيدو"},
                {"id": "19391", "label": "أخرى"}
            ]
        }
    }
}
"""

data = json.loads(WATCHES_JSON)
brands = data['result']['data']['values']

generated_tuples = [
    '    # ═══════════════════════════════════════════════',
    '    # THIRD-LEVEL — ساعات ذكية (parent=430)',
    '    # ═══════════════════════════════════════════════'
]

for brand in brands:
    brand_id = brand['id']
    brand_name = brand['label'].replace('"', '\\"')
    generated_tuples.append(f'    ({brand_id}, 430, "{brand_name}", "ساعات {brand_name}", "watch", None, None, {{"en": ["{brand_name}"]}}),')

generated_tuples.append('')

print(f"Generated {len(brands)} watch brands")

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "THIRD-LEVEL — ساعات ذكية (parent=430)" in line and start_idx == -1:
        start_idx = i - 1
    if "THIRD-LEVEL — اساور رياضية (parent=440)" in line and start_idx != -1:
        end_idx = i - 1
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + generated_tuples + lines[end_idx:]
    with open('seed_categories.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("seed_categories.py updated successfully!")
else:
    print(f"Error: Could not find insertion boundaries: start={start_idx}, end={end_idx}")

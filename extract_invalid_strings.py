import json

with open('invalid_locations_in_db.json', 'r', encoding='utf-8') as f:
    invalid_locations = json.load(f)

# invalid_locations is a list of dicts: {"location": "عمان, صويفية", "count": 5}
with open('invalid_strings_only.txt', 'w', encoding='utf-8') as f:
    for item in invalid_locations:
        loc = item['location']
        if loc:  # skip None or empty
            f.write(loc + '\n')

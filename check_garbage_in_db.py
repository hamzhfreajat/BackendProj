import json

with open('cleaned_user_regions.json', 'r', encoding='utf-8') as f:
    cleaned_mappings = json.load(f)

existing_regions = set()
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        l = line.strip()
        if l:
            existing_regions.add(l)

found_garbage = []
for garbage_string in cleaned_mappings.keys():
    if garbage_string in existing_regions:
        found_garbage.append(garbage_string)

print(f"Out of {len(cleaned_mappings)} garbage strings, {len(found_garbage)} are still sitting in all_regions_db.txt!")

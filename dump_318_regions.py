import json

# Read the last 318 lines from all_regions_db.txt directly (which we appended in apply_extracted_regions.py)
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

new_lines = lines[-318:]
for i, line in enumerate(new_lines):
    print(f"{i+1}. {line}")

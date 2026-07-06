import re
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    raw_text = f.read().strip()

with open('extraction_constants.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'LOCATIONS = \"\"\"[\s\S]*?\"\"\"', f'LOCATIONS = \"\"\"{raw_text}\"\"\"', text)

with open('extraction_constants.py', 'w', encoding='utf-8') as f:
    f.write(text)

import json

with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

new_lines = lines[-318:]
with open('new_318_utf8.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

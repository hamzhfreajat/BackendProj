import json
import psycopg2
import os

try:
    with open('region_corrections.json', 'r', encoding='utf-8') as f:
        corrections = json.load(f)
except FileNotFoundError:
    print("No corrections file found. Exiting.")
    exit(0)

# Connect to DB
conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()

updated_ads_count = 0

for old_str, new_str in corrections.items():
    if '|' not in old_str or '|' not in new_str:
        continue
    
    old_city, old_region = old_str.split('|', 1)
    new_city, new_region = new_str.split('|', 1)
    
    old_location = f"{old_city}, {old_region}"
    new_location = f"{new_city}, {new_region}"
    
    cur.execute("UPDATE ads SET location = %s WHERE location = %s", (new_location, old_location))
    updated_ads_count += cur.rowcount

conn.commit()
conn.close()

# Now update all_regions_db.txt
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

new_lines = []
for line in lines:
    l = line.strip()
    if not l:
        continue
    if l in corrections:
        corrected = corrections[l].strip()
        if corrected:
            new_lines.append(corrected)
    else:
        new_lines.append(l)

# Deduplicate
unique_lines = list(dict.fromkeys(new_lines))

with open('../all_regions_db.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(unique_lines))

print(f"Updated {updated_ads_count} ads in DB.")
print(f"Removed {(len(lines) - len(unique_lines))} duplicates/corrected regions from all_regions_db.txt.")

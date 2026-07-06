import json
import psycopg2

# 1. Load valid locations from all_regions_db.txt
valid_locations = set()
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        l = line.strip()
        if '|' in l:
            city, reg = l.split('|', 1)
            valid_locations.add(f"{city.strip()}|{reg.strip()}")

# 2. Load the mapping from the subagent
try:
    with open('db_corrections_map.json', 'r', encoding='utf-8') as f:
        corrections_map = json.load(f)
except FileNotFoundError:
    print("Corrections map not found. Exiting.")
    exit(1)

# 3. Load the invalid locations we identified
with open('invalid_locations_in_db.json', 'r', encoding='utf-8') as f:
    invalid_data = json.load(f)

conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()

total_updated = 0
fallback_count = 0
mapped_count = 0

for item in invalid_data:
    original_loc = item['location']
    if not original_loc or ',' not in original_loc:
        continue
    
    orig_city, orig_region = original_loc.split(',', 1)
    orig_city = orig_city.strip()
    
    proposed_map = corrections_map.get(original_loc)
    
    new_location = None
    if proposed_map and proposed_map != 'null' and '|' in proposed_map:
        # Check if the proposed map strictly exists in valid_locations
        if proposed_map in valid_locations:
            p_city, p_reg = proposed_map.split('|', 1)
            new_location = f"{p_city.strip()}, {p_reg.strip()}"
            mapped_count += item['count']
            
    if not new_location:
        # Fallback to City, أخرى
        new_location = f"{orig_city}, أخرى"
        fallback_count += item['count']
        
    cur.execute("UPDATE ads SET location = %s WHERE location = %s", (new_location, original_loc))
    total_updated += cur.rowcount

conn.commit()
conn.close()

print(f"Migration complete.")
print(f"Ads successfully mapped to a strict formal region: {mapped_count}")
print(f"Ads fallen back to '[City], أخرى': {fallback_count}")
print(f"Total rows updated in DB: {total_updated}")

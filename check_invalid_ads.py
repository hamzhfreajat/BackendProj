import psycopg2

# 1. Load valid locations from all_regions_db.txt
valid_locations = set()
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        l = line.strip()
        if '|' in l:
            city, reg = l.split('|', 1)
            valid_locations.add(f"{city.strip()}, {reg.strip()}")

# 2. Query all unique locations from ads table
conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()
cur.execute("SELECT location, COUNT(*) FROM ads GROUP BY location")
rows = cur.fetchall()
conn.close()

invalid_locations = []
total_invalid_ads = 0

for loc, count in rows:
    # Ads might be 'City, أخرى' which is a valid fallback
    if loc and not loc.endswith(', أخرى'):
        # Check if exactly matches
        if loc not in valid_locations:
            invalid_locations.append((loc, count))
            total_invalid_ads += count

# Save the invalid ones to a JSON file for analysis
import json
with open('invalid_locations_in_db.json', 'w', encoding='utf-8') as f:
    json.dump([{"location": loc, "count": c} for loc, c in invalid_locations], f, ensure_ascii=False, indent=2)

print(f"Total valid regions in text file: {len(valid_locations)}")
print(f"Total unique invalid locations in DB: {len(invalid_locations)}")
print(f"Total ads with invalid locations: {total_invalid_ads}")

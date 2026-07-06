import json
import psycopg2

# 1. Read existing regions
existing_regions = set()
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if '|' in line:
            city, region = line.split('|', 1)
            existing_regions.add((city.strip(), region.strip()))

# 2. Read final extracted
with open('final_extracted_regions.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# 3. Connect to DB
conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()

new_regions_added = set()
updated_count = 0

for item in results:
    ad_id = item['id']
    city = item['city']
    region = item['region']
    
    # Check if region is known
    # First exact match
    if (city, region) not in existing_regions:
        if (city, region) not in new_regions_added:
            new_regions_added.add((city, region))
            with open('../all_regions_db.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{city}|{region}")
            
    # Update DB
    new_location = f"{city}, {region}"
    cur.execute("UPDATE ads SET location = %s WHERE id = %s", (new_location, ad_id))
    updated_count += 1

conn.commit()
conn.close()

print(f"Updated {updated_count} ads in the database.")
print(f"Added {len(new_regions_added)} new regions to all_regions_db.txt.")

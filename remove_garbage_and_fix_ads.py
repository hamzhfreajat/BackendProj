import json
import psycopg2
import re

# 1. Load garbage strings and mappings
with open('cleaned_user_regions.json', 'r', encoding='utf-8') as f:
    cleaned_mappings = json.load(f)

# 2. Clean all_regions_db.txt
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

clean_lines = []
for line in lines:
    l = line.strip()
    if not l: continue
    # If this line is one of the garbage strings, DROP IT
    if l in cleaned_mappings:
        continue
    clean_lines.append(l)

# Save cleaned DB
with open('../all_regions_db.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(clean_lines))

# 3. Update constants so frontend gets the fix instantly
raw_text = '\n'.join(clean_lines)
with open('extraction_constants.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = re.sub(r'LOCATIONS = \"\"\"[\s\S]*?\"\"\"', f'LOCATIONS = \"\"\"{raw_text}\"\"\"', text)
with open('extraction_constants.py', 'w', encoding='utf-8') as f:
    f.write(text)

# 4. Connect to PostgreSQL to fix the ads that were using these garbage strings
conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()

valid_locations_set = set(clean_lines)

total_ads_fixed = 0

for garbage_string, mapped_string in cleaned_mappings.items():
    if '|' not in garbage_string: continue
    g_city, g_reg = garbage_string.split('|', 1)
    garbage_db_loc = f"{g_city}, {g_reg}"
    
    new_db_loc = f"{g_city}, أخرى" # fallback
    
    if mapped_string and mapped_string != 'null' and '|' in mapped_string:
        if mapped_string in valid_locations_set:
            m_city, m_reg = mapped_string.split('|', 1)
            new_db_loc = f"{m_city}, {m_reg}"
            
    cur.execute("UPDATE ads SET location = %s WHERE location = %s", (new_db_loc, garbage_db_loc))
    total_ads_fixed += cur.rowcount

conn.commit()
conn.close()

print(f"Removed {len(cleaned_mappings)} garbage strings from all_regions_db.txt")
print(f"Fixed {total_ads_fixed} ads in PostgreSQL that were using these garbage strings.")

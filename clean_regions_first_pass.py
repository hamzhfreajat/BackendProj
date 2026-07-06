import json

lines = []
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        l = line.strip()
        if l:
            lines.append(l)

# 1. Exact duplicates
unique_lines = list(dict.fromkeys(lines))

# 2. Let's find suspicious duplicates (same region, multiple cities)
region_to_cities = {}
for line in unique_lines:
    if '|' in line:
        city, region = line.split('|', 1)
        if region not in region_to_cities:
            region_to_cities[region] = []
        region_to_cities[region].append(city)

suspicious = {reg: cities for reg, cities in region_to_cities.items() if len(cities) > 1}

# Save deduplicated to a temp file
with open('../all_regions_db_deduped.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(unique_lines))

with open('suspicious_regions.txt', 'w', encoding='utf-8') as f:
    for reg, cities in suspicious.items():
        f.write(f"Region: {reg} -> Cities: {', '.join(cities)}\n")

print(f"Original lines: {len(lines)}")
print(f"Unique lines: {len(unique_lines)}")
print(f"Suspicious regions (in multiple cities): {len(suspicious)}")

import json
import os

# 1. Standardize all_regions_db.txt
standardized_existing = set()
lines_to_write = []

with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

for line in lines:
    l = line.strip()
    if not l:
        continue
    if '|' in l:
        city, region = l.split('|', 1)
        # remove spaces around pipe
        city = city.strip()
        region = region.strip()
        norm_line = f"{city}|{region}"
        if norm_line not in standardized_existing:
            standardized_existing.add(norm_line)
            lines_to_write.append(norm_line)

# overwrite DB to be standardized
with open('../all_regions_db.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines_to_write))

# 2. Filter cleaned regions
with open('cleaned_user_regions.json', 'r', encoding='utf-8') as f:
    cleaned_mappings = json.load(f)

final_filtered = set()
for raw_string, cleaned_region in cleaned_mappings.items():
    if cleaned_region and cleaned_region != 'null':
        if '|' in cleaned_region:
            c, r = cleaned_region.split('|', 1)
            norm_clean = f"{c.strip()}|{r.strip()}"
            if norm_clean not in standardized_existing:
                final_filtered.add(norm_clean)

artifact_dir = r"C:\Users\hfraijat\.gemini\antigravity\brain\4a8b2407-cea4-417b-a807-1532f048301a"
os.makedirs(artifact_dir, exist_ok=True)
artifact_path = os.path.join(artifact_dir, "filtered_clean_regions.md")

with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write("# Filtered Clean Regions (Strict Verification)\n")
    f.write("Here are the regions from your list that represent valid formal locations AND are currently strictly missing from the database (all spaces ignored):\n\n")
    if not final_filtered:
        f.write("*None! All the valid formal locations from your list already exist in the database.*")
    else:
        for r in sorted(final_filtered):
            f.write(f"- {r}\n")

print(f"Artifact created at {artifact_path}")
print(f"Total genuinely missing regions: {len(final_filtered)}")

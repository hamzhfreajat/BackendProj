import json
import os

with open('cleaned_user_regions.json', 'r', encoding='utf-8') as f:
    cleaned_mappings = json.load(f)

# Load existing database regions
existing_regions = set()
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        l = line.strip()
        if l:
            existing_regions.add(l)

final_filtered = set()
for raw_string, cleaned_region in cleaned_mappings.items():
    if cleaned_region and cleaned_region != 'null':
        # If the cleaned formal region is missing from our database
        if cleaned_region not in existing_regions:
            final_filtered.add(cleaned_region)

artifact_dir = r"C:\Users\hfraijat\.gemini\antigravity\brain\4a8b2407-cea4-417b-a807-1532f048301a"
os.makedirs(artifact_dir, exist_ok=True)
artifact_path = os.path.join(artifact_dir, "filtered_clean_regions.md")

with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write("# Filtered Clean Regions\n")
    f.write("Here are the regions from your list that represent valid formal locations AND are currently missing from the database:\n\n")
    if not final_filtered:
        f.write("*None! All the valid formal locations from your list already exist in the database.*")
    else:
        for r in sorted(final_filtered):
            f.write(f"- {r}\n")

print(f"Artifact created at {artifact_path}")

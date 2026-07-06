import json
from collections import defaultdict
import os

with open('final_extracted_regions.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Group unique regions by city
city_regions = defaultdict(set)
for item in results:
    if item['region'] and item['region'] != 'null':
        city_regions[item['city']].add(item['region'])

# Generate Markdown
md_lines = []
md_lines.append("# Newly Discovered Regions from 'Others' (أخرى)")
md_lines.append("\nHere are the new regions that my LLM engine successfully extracted from the 698 ads. These ads had their location updated in the database from `[City], أخرى` to `[City], [Region]`. These regions were also appended to `all_regions_db.txt` so the scraper will automatically recognize them going forward.\n")

total_regions = sum(len(regs) for regs in city_regions.values())
md_lines.append(f"**Total New Unique Regions Created:** {total_regions}\n")

for city, regions in sorted(city_regions.items()):
    md_lines.append(f"### {city} ({len(regions)} regions)")
    for r in sorted(regions):
        md_lines.append(f"- {r}")
    md_lines.append("")

artifact_dir = r"C:\Users\hfraijat\.gemini\antigravity\brain\4a8b2407-cea4-417b-a807-1532f048301a"
os.makedirs(artifact_dir, exist_ok=True)
artifact_path = os.path.join(artifact_dir, "new_regions_report.md")

with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))

print(f"Report generated at: {artifact_path}")

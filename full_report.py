import json
with open('region_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

md = '# Full Region Analysis Report\n\n'
md += '## ?? Invalid or Poorly Named Regions (87 found)\n'
md += 'These regions contain directional terms, landmarks, or are too short to be considered proper geographic regions. You may want to delete or rename them.\n\n'
md += '| ID | Region Name |\n|---|---|\n'
for r in data['invalid_regions']:
    md += f'| {r["id"]} | {r["name"]} |\n'

md += '\n## ? Exact Duplicates (81 groups)\n'
md += 'These are regions with the exact same Arabic name but different IDs.\n\n'
for k, v in data['exact_duplicates'].items():
    ids = [str(r["id"]) for r in v]
    md += f'- **{k}**: IDs: {", ".join(ids)}\n'

md += '\n## ?? Near Duplicates (52 groups)\n'
md += 'These regions have different spelling but normalize to the same name (e.g. ???? vs ???? or ??? ?????? vs ???).\n\n'
for k, v in data['normalized_duplicates'].items():
    items = [f"{r['name']} (ID: {r['id']})" for r in v]
    md += f'- **{k}**: {", ".join(items)}\n'

with open(r'C:\Users\hfraijat\.gemini\antigravity\brain\b5c78e29-59b6-45e8-ab63-050645670f8a\full_regions_report.md', 'w', encoding='utf-8') as f:
    f.write(md)

import json
with open('region_analysis.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

md = '# Duplicate Regions (Names Only)\n\n'

md += '## ? Exact Duplicates (81 groups)\n'
md += 'These region names appear multiple times in the database:\n\n'
for k, v in data['exact_duplicates'].items():
    md += f'- **{k}** (Repeated {len(v)} times)\n'

md += '\n## ?? Near Duplicates (52 groups)\n'
md += 'These regions have different spelling variations but mean the same thing:\n\n'
for k, v in data['normalized_duplicates'].items():
    unique_names = list(set([r['name'] for r in v]))
    md += f'- **{k}**: {", ".join(unique_names)}\n'

with open(r'C:\Users\hfraijat\.gemini\antigravity\brain\b5c78e29-59b6-45e8-ab63-050645670f8a\simple_regions_report.md', 'w', encoding='utf-8') as f:
    f.write(md)

import json

with open('debug_others.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('../analysis_results.md', 'w', encoding='utf-8') as md:
    md.write('# Analysis of Ads mapped to Others\n\n')
    md.write(f'**Total Ads in Other:** {data["total_others"]}\n\n')
    md.write('## Sample Ads\n\n')
    for ad in data['samples'][:30]:
        md.write(f'- **ID**: {ad["id"]}\n')
        md.write(f'- **Location**: {ad["location"]}\n')
        md.write(f'- **Title**: {ad["title"]}\n')
        md.write(f'- **Raw**: {ad["raw_snippet"]}\n\n')

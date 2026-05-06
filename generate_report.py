import json

with open('test_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

md = '# 🧠 Advanced NLP Search Test Results\n\n'
md += 'Below is the full output of the 138 real-world test queries provided, showcasing the new parsing engine logic:\n\n'
md += '| Search Query | Core Filters | Soft Filters (Rank Boost) | Matching Ad Count |\n'
md += '| :--- | :--- | :--- | :--- |\n'

for r in results:
    q = r['query']
    p = r['parsed']
    count = r['count']
    
    core = []
    if p.get('property_type'): core.append(f'`{p["property_type"]}`')
    if p.get('location'): core.append(f'in `{p["location"]}`')
    if p.get('deal_type'): core.append(f'for `{p["deal_type"]}`')
    if p.get('bedrooms'): core.append(f'`{p["bedrooms"]} Beds`')
    if p.get('max_price'): core.append(f'`< {p["max_price"]}`')
    
    soft = []
    if p.get('features'): soft.append(f'`Feat:` {", ".join(p["features"])}')
    if p.get('intents'): soft.append(f'`Intents:` {", ".join(p["intents"])}')
    if p.get('legal'): soft.append(f'`Legal:` {", ".join(p["legal"])}')
    
    core_str = " <br> ".join(core) if core else "-"
    soft_str = " <br> ".join(soft) if soft else "-"
    
    md += f'| **{q}** | {core_str} | {soft_str} | **{count}** |\n'

with open('C:/Users/hfraijat/.gemini/antigravity/brain/74ad83ee-dd3d-4040-9a4f-a3cf6e2796b6/nlp_search_results.md', 'w', encoding='utf-8') as f:
    f.write(md)

print("Report generated successfully.")

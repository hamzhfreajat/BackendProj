import json
with open('test_bulk_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for d in data[:30]:
    print(f"{d['query']} => Cat: {d['category_id']} ({d['category_name']})")

import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('d:/open/classifieds-app/backend/review_chunk_4.json', encoding='utf-8') as f:
    ads = json.load(f)

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else 25

for i in range(start, min(end, len(ads))):
    ad = ads[i]
    print(f"--- Index {i} | ID: {ad['id']} ---")
    print(f"TITLE: {ad['title']}")
    print(f"DESC:  {ad['desc'][:200]}...")
    print(f"CANDIDATES: {ad['matched']}\n")

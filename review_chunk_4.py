import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('d:/open/classifieds-app/backend/valid_locations.json', encoding='utf-8') as f:
    valid_locations = json.load(f)

with open('d:/open/classifieds-app/backend/others_chunk_4.json', encoding='utf-8') as f:
    ads = json.load(f)

def norm(text):
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[أإآآ]', 'ا', text)
    text = re.sub(r'ة\b', 'ه', text)
    text = re.sub(r'ى\b', 'ي', text)
    text = re.sub(r'[\s_,\-\./\\()|#]+', ' ', text)
    return text.strip().lower()

# Map normalized location strings to exact valid location format
valid_norm_map = {}
valid_by_city = {}

for loc in valid_locations:
    c, d = [x.strip() for x in loc.split(',', 1)]
    nc, nd = norm(c), norm(d)
    valid_norm_map[(nc, nd)] = loc
    if nc not in valid_by_city:
        valid_by_city[nc] = []
    valid_by_city[nc].append((loc, d, nd))

out_review = []

for ad in ads:
    ad_id = str(ad['id'])
    title = ad.get('title', '')
    desc = ad.get('desc', '')
    full_text = title + " " + desc
    nt = norm(full_text)
    
    matched = []
    for (nc, nd), orig in valid_norm_map.items():
        if nd != norm("أخرى") and len(nd) > 1:
            if nd in nt:
                city_in = nc in nt
                matched.append((orig, city_in, len(nd)))
    
    # Sort matches by whether city is mentioned, then length of district string
    matched.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    out_review.append({
        'id': ad_id,
        'title': title,
        'desc': desc,
        'matched': [m[0] for m in matched[:5]]
    })

with open('d:/open/classifieds-app/backend/review_chunk_4.json', 'w', encoding='utf-8') as f:
    json.dump(out_review, f, ensure_ascii=False, indent=2)

print(f"Generated review_chunk_4.json with {len(out_review)} ads.")

import json
import re

def normalize_arabic(text):
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u0652]', '', text) # remove tashkeel
    text = re.sub(r'[أإآآ]', 'ا', text)
    text = re.sub(r'ة\b', 'ه', text)
    text = re.sub(r'ى\b', 'ي', text)
    text = re.sub(r'[\s_]+', ' ', text)
    return text.strip().lower()

with open('d:/open/classifieds-app/backend/valid_locations.json', encoding='utf-8') as f:
    valid_locs = json.load(f)

with open('d:/open/classifieds-app/backend/others_chunk_4.json', encoding='utf-8') as f:
    ads = json.load(f)

# Build search structures
loc_info = []
for loc in valid_locs:
    parts = loc.split(',')
    city = parts[0].strip()
    dist = parts[1].strip()
    
    norm_city = normalize_arabic(city)
    norm_dist = normalize_arabic(dist)
    norm_full = norm_city + " " + norm_dist
    
    loc_info.append({
        'original': loc,
        'city': city,
        'dist': dist,
        'norm_city': norm_city,
        'norm_dist': norm_dist,
        'norm_full': norm_full
    })

results = {}

for ad in ads:
    ad_id = str(ad['id'])
    title = ad.get('title', '')
    desc = ad.get('desc', '')
    full_text = title + " " + desc
    norm_text = normalize_arabic(full_text)
    
    # Let's find matches
    matches = []
    
    # 1. Direct full match (norm_dist in norm_text AND norm_city in norm_text)
    for info in loc_info:
        # Check if dist is meaningful (not أخرى)
        dist = info['dist']
        norm_dist = info['norm_dist']
        norm_city = info['norm_city']
        
        if dist == "أخرى":
            continue
            
        # Match district name
        if norm_dist in norm_text:
            # Check if city matches or is implied or in text
            city_present = norm_city in norm_text
            matches.append((info['original'], norm_dist, city_present, len(norm_dist)))
            
    # Sort matches by length of district name (longer district names are more specific)
    matches.sort(key=lambda x: (x[2], x[3]), reverse=True)
    
    results[ad_id] = {
        'id': ad_id,
        'title': title,
        'desc': desc[:120],
        'matches': [m[0] for m in matches[:5]]
    }

print("Sample matching results:")
for ad_id in list(results.keys())[:15]:
    r = results[ad_id]
    print(f"ID {ad_id}: Title: {r['title']}")
    print(f"   Matches: {r['matches']}\n")

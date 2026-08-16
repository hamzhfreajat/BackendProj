import json
import sys
import re

def normalize(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[\u064B-\u0652]', '', text)
    return text

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('valid_locations.json', 'r', encoding='utf-8') as f:
        valid_locations = json.load(f)

    with open('others_chunk_10.json', 'r', encoding='utf-8') as f:
        ads = json.load(f)

    # Build mapping from normalized representations of valid locations
    valid_map = {} # normalized_full -> original
    area_map = {}  # normalized_area -> list of (gov, original_full)
    
    for loc in valid_locations:
        parts = loc.split(',')
        gov = parts[0].strip()
        area = parts[1].strip() if len(parts) > 1 else ""
        
        norm_full = normalize(loc)
        valid_map[norm_full] = loc
        
        norm_area = normalize(area)
        if norm_area not in area_map:
            area_map[norm_area] = []
        area_map[norm_area].append((gov, loc))

    print(f"Loaded {len(valid_locations)} valid locations.")
    
    results = []

    for idx, ad in enumerate(ads):
        ad_id = str(ad.get("id"))
        title = ad.get("title", "")
        desc = ad.get("desc", "")
        full_text = f"{title}\n{desc}"
        norm_text = normalize(full_text)

        # Let's collect potential area matches
        found_matches = []
        
        # Check direct full location matches
        for norm_full, orig_loc in valid_map.items():
            if norm_full in norm_text:
                found_matches.append((orig_loc, "exact_full"))

        # Check area matches
        for norm_area, loc_list in area_map.items():
            if not norm_area or len(norm_area) < 3 or norm_area == 'اخري':
                continue
            # Use word boundary or substring check carefully
            pattern = r'(?:\b|_|\s|^)' + re.escape(norm_area) + r'(?:\b|_|\s|$)'
            if re.search(pattern, norm_text):
                for gov, orig_loc in loc_list:
                    # check if governorate is also in text or if unique area
                    found_matches.append((orig_loc, f"area_match:{norm_area}"))

        results.append({
            "idx": idx,
            "id": ad_id,
            "title": title,
            "desc": desc,
            "candidates": list(set(found_matches))
        })

    with open('candidates_chunk10.json', 'w', encoding='utf-8') as out:
        json.dump(results, out, ensure_ascii=False, indent=2)

    print("Candidates written to candidates_chunk10.json")

if __name__ == '__main__':
    main()

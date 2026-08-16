import json
import sys
import re

def normalize(text):
    if not text:
        return ""
    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[\u064B-\u0652]', '', text) # remove tashkeel
    return text

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('valid_locations.json', 'r', encoding='utf-8') as f:
        valid_locations = json.load(f)

    with open('others_chunk_10.json', 'r', encoding='utf-8') as f:
        ads = json.load(f)

    # Build maps
    full_norm_to_orig = {}
    area_norm_to_origs = {} # area_norm -> list of (gov, orig_loc)

    for loc in valid_locations:
        parts = loc.split(',')
        gov = parts[0].strip()
        area = parts[1].strip() if len(parts) > 1 else ""
        
        norm_full = normalize(loc)
        full_norm_to_orig[norm_full] = loc
        
        norm_area = normalize(area)
        if norm_area not in area_norm_to_origs:
            area_norm_to_origs[norm_area] = []
        area_norm_to_origs[norm_area].append((gov, loc))

    gov_list = ['عمان', 'إربد', 'اربد', 'الزرقاء', 'السلط', 'مادبا', 'العقبة', 'المفرق', 'جرش', 'الكرك', 'عجلون', 'معان', 'الطفيلة']

    analysis_lines = []
    final_output = {}

    for idx, ad in enumerate(ads):
        ad_id = str(ad.get("id"))
        title = ad.get("title", "")
        desc = ad.get("desc", "")
        full_text = f"{title}\n{desc}"
        norm_full_text = normalize(full_text)

        analysis_lines.append(f"=== INDEX {idx} | ID: {ad_id} ===")
        analysis_lines.append(f"TITLE: {title}")
        analysis_lines.append(f"DESC: {desc[:250]}...")

        # We will determine the status and location
        # Let's inspect candidates and write detailed candidate lists
        matched_candidates = []

        # Direct full location match
        for norm_full, orig_loc in full_norm_to_orig.items():
            if norm_full in norm_full_text:
                matched_candidates.append((orig_loc, "exact_full_norm", len(orig_loc)))

        # Area matches
        for norm_area, loc_tuple_list in area_norm_to_origs.items():
            if not norm_area or norm_area == 'اخري' or len(norm_area) < 3:
                continue
            
            # regex for area match
            pattern = r'(?:\b|_|\s|^)' + re.escape(norm_area) + r'(?:\b|_|\s|$)'
            if re.search(pattern, norm_full_text):
                for gov, orig_loc in loc_tuple_list:
                    # check if governorate is also mentioned in text
                    gov_norm = normalize(gov)
                    score = len(orig_loc)
                    if gov_norm in norm_full_text:
                        score += 100
                    matched_candidates.append((orig_loc, f"area:{norm_area}", score))

        # Sort candidates by score descending
        matched_candidates.sort(key=lambda x: x[2], reverse=True)
        unique_cands = []
        seen = set()
        for cand, src, score in matched_candidates:
            if cand not in seen:
                seen.add(cand)
                unique_cands.append(f"{cand} ({src}, score={score})")

        analysis_lines.append(f"CANDIDATES: {unique_cands[:5]}")
        analysis_lines.append("\n")

    with open('full_chunk10_analysis.txt', 'w', encoding='utf-8') as out:
        out.write("\n".join(analysis_lines))

    print(f"Analysis written to full_chunk10_analysis.txt")

if __name__ == '__main__':
    main()

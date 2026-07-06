from extraction_constants import LOCATIONS, REAL_ESTATE_CATEGORIES

def get_location_map():
    # Parse LOCATIONS string into dict
    locations = {}
    lines = LOCATIONS.split("\n")
    for line in lines:
        if line.startswith("CITY: "):
            parts = line.replace("CITY: ", "").split(" -> REGIONS: [")
            city = parts[0].strip()
            regions_str = parts[1].replace("]", "").strip()
            regions = [r.strip() for r in regions_str.split(",") if r.strip()]
            locations[city] = regions
    return locations

import re
def normalize_arabic(text):
    if not text: return ""
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ي$', 'ى', text)
    return text

def get_category_map():
    # Parse REAL_ESTATE_CATEGORIES string into dict
    categories = {}
    lines = REAL_ESTATE_CATEGORIES.split("\n")
    for line in lines:
        if line.startswith("ID: "):
            parts = line.replace("ID: ", "").split(" | ", 1)
            cat_id = int(parts[0].strip())
            cat_name = parts[1].strip()
            categories[cat_name] = cat_id
    return categories

import json
import os

def load_overrides():
    overrides_path = os.path.join(os.path.dirname(__file__), 'location_overrides.json')
    try:
        with open(overrides_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

LOCATION_OVERRIDES = load_overrides()

def get_dynamic_location_rules():
    if not LOCATION_OVERRIDES:
        return ""
    rules = []
    for i, (k, v) in enumerate(LOCATION_OVERRIDES.items(), 1):
        rules.append(f"    - If the text mentions '{k}', you MUST map it strictly to '{v}'.")
    return "\n".join(rules)

def map_location(ai_location_str, city_regions_map):
    if not ai_location_str:
        return ""
        
    ai_loc = ai_location_str.strip()
    
    # Check overrides first
    for key, value in LOCATION_OVERRIDES.items():
        if key in ai_loc:
            return value

    ai_loc_norm = normalize_arabic(ai_loc).replace(" ", "")
    
    # Simple substring matching
    for city, regions in city_regions_map.items():
        city_norm = normalize_arabic(city).replace(" ", "")
        
        # Sort regions by length descending to match more specific regions first (e.g. "شفا بدران" before "بدر")
        for req in sorted(regions, key=len, reverse=True):
            req_norm = normalize_arabic(req).replace(" ", "")
            if req_norm in ai_loc_norm or (len(ai_loc_norm)>3 and ai_loc_norm in req_norm):
                return f"{city}, {req}"
                
        # Then check if city matches
        if city_norm in ai_loc_norm:
            return f"{city}, أخرى"
            
    return ""

def map_location_with_fallback(ai_location_str, raw_description, city_regions_map, fallback_city):
    primary_map = map_location(ai_location_str, city_regions_map)
    
    if primary_map and not primary_map.endswith("أخرى"):
        return primary_map

    # Safety Net Scanner: scan raw text for valid regions in fallback_city
    if raw_description and fallback_city in city_regions_map:
        raw_norm = normalize_arabic(raw_description).replace(" ", "")
        
        valid_regions = city_regions_map[fallback_city]
        
        for req in sorted(valid_regions, key=len, reverse=True):
            req_norm = normalize_arabic(req).replace(" ", "")
            if len(req_norm) > 3 and req_norm in raw_norm:
                return f"{fallback_city}, {req}"

    if primary_map:
        return primary_map

    return f"{fallback_city}, أخرى"

def map_category(ai_category_str, categories_map):
    if not ai_category_str:
        return 0
        
    ai_cat = ai_category_str.strip()
    
    # Exact match
    if ai_cat in categories_map:
        return categories_map[ai_cat]
        
    # Substring match
    for cat_name, cat_id in categories_map.items():
        if cat_name in ai_cat or ai_cat in cat_name:
            return cat_id
            
    # Fallback to general categories dynamically based on keywords
    if "بيع" in ai_cat:
        return 2 # General Sale
    elif "ايجار" in ai_cat or "إيجار" in ai_cat:
        return 3 # General Rent
    elif "ارض" in ai_cat or "أرض" in ai_cat or "اراضي" in ai_cat:
        return 10313 # Lands
        
    return 3 # Fallback rent

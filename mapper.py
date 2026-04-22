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

def map_location(ai_location_str, city_regions_map):
    if not ai_location_str:
        return ""
        
    ai_loc = ai_location_str.strip()
    
    # Simple substring matching
    for city, regions in city_regions_map.items():
        # First check if any region matches
        for req in regions:
            if req in ai_loc:
                return f"{city}, {req}"
        # Then check if city matches
        if city in ai_loc:
            return f"{city}, أخرى"
            
    return ""

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

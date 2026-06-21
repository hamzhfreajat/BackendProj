import sys

def fix_file():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We need to replace the garbled block with the correct code
    # We can just look for '# Handle automatic region creation if location specifies a new region'
    import re
    
    correct_block = '''    # Handle automatic region creation if location specifies a new region
    if "location" in update_dict and update_dict["location"]:
        loc_str = update_dict["location"].strip()
        if "," in loc_str or "،" in loc_str:
            parts = [p.strip() for p in loc_str.replace("،", ",").split(",")]
            if len(parts) >= 2:
                city_name = parts[0]
                region_name = parts[1]
                
                c_norm = norm_str(city_name)
                if c_norm == norm_str("محافظة العاصمة"): c_norm = norm_str("عمان")
                elif c_norm.startswith(norm_str("محافظة ")): c_norm = c_norm.replace(norm_str("محافظة "), "")
                
                city = db.query(models.City).filter(norm_col(models.City.name_ar) == c_norm).first()
                if city:
                    r_norm = norm_str(region_name)
                    region = db.query(models.Region).filter(
                        models.Region.city_id == city.id,
                        norm_col(models.Region.name_ar) == r_norm
                    ).first()
                    
                    if not region:
                        new_region = models.Region(
                            city_id=city.id,
                            name_ar=region_name,
                            name_en=region_name
                        )
                        db.add(new_region)'''
                        
    # Replace from that comment until 'was_unpublished'
    pattern = r'# Handle automatic region creation if location specifies a new region.*?was_unpublished'
    new_content = re.sub(pattern, correct_block + '\n\n    was_unpublished', content, flags=re.DOTALL)
    
    # Also check line 1025 for only_others logic which also had Arabic
    pattern_others = r'if only_others:.*?models\.Ad\.location\.ilike\("%other%"\)\s*\)\)'
    correct_others = '''if only_others:
        query = query.filter(or_(
            models.Ad.location.ilike("%أخرى%"),
            models.Ad.location.ilike("%اخرى%"),
            models.Ad.location.ilike("%other%")
        ))'''
    new_content = re.sub(pattern_others, correct_others, new_content, flags=re.DOTALL)
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
fix_file()

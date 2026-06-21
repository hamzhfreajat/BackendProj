import sys

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '# Handle automatic region creation' in line:
        skip = True
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
                        db.add(new_region)
'''
        new_lines.append(correct_block)
    elif 'was_unpublished = not db_ad.is_published' in line and skip:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

final_lines = []
skip_others = False
for line in new_lines:
    if 'if only_others:' in line:
        skip_others = True
        correct_others = '''    if only_others:
        query = query.filter(or_(
            models.Ad.location.ilike("%أخرى%"),
            models.Ad.location.ilike("%اخرى%"),
            models.Ad.location.ilike("%other%")
        ))
'''
        final_lines.append(correct_others)
    elif skip_others and 'if min_price is not None:' in line:
        skip_others = False
        final_lines.append(line)
    elif not skip_others:
        final_lines.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

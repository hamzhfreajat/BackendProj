import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    if image_urls:
        update_dict["image_url"] = image_urls[0]

    was_unpublished = not db_ad.is_published'''

replacement = '''    if image_urls:
        update_dict["image_url"] = image_urls[0]

    # Handle automatic region creation if location specifies a new region
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

    was_unpublished = not db_ad.is_published'''

if target in content:
    new_content = content.replace(target, replacement)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS")
else:
    print("TARGET NOT FOUND")

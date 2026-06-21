from database import SessionLocal
from models import City, Region

def norm_str(s):
    if not s: return s
    for a, b in [('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا'), ('ة', 'ه'), ('ي', 'ى')]:
        s = s.replace(a, b)
    return s

def norm_col(col):
    from sqlalchemy.sql import func
    c = func.replace(col, 'أ', 'ا')
    c = func.replace(c, 'إ', 'ا')
    c = func.replace(c, 'آ', 'ا')
    c = func.replace(c, 'ة', 'ه')
    c = func.replace(c, 'ي', 'ى')
    return c

db = SessionLocal()

loc_str = "إربد , المقابلة".strip()
loc_str = loc_str.replace("،", ",").replace("-", ",").replace(" - ", ",")
parts = [p.strip() for p in loc_str.split(",")]

output = f"Parts: {parts}\n"

if len(parts) >= 2:
    city_name = parts[0]
    region_name = parts[1]
    
    c_norm = norm_str(city_name)
    output += f"City Name: {city_name}, c_norm: {c_norm}\n"
    
    if c_norm == norm_str("محافظة العاصمة"): c_norm = norm_str("عمان")
    elif c_norm.startswith(norm_str("محافظة ")): c_norm = c_norm.replace(norm_str("محافظة "), "")
    
    city = db.query(City).filter(norm_col(City.name_ar) == c_norm).first()
    output += f"City matched: {city.name_ar if city else 'None'}\n"
    
    if city:
        r_norm = norm_str(region_name)
        output += f"Region Name: {region_name}, r_norm: {r_norm}\n"
        region = db.query(Region).filter(
            Region.city_id == city.id,
            norm_col(Region.name_ar) == r_norm
        ).first()
        
        output += f"Region matched: {region.name_ar if region else 'None'}\n"
        
        if not region:
            output += "Action: WOULD CREATE REGION\n"

with open('debug2.txt', 'w', encoding='utf-8') as f:
    f.write(output)

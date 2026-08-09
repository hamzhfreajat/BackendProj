from database import SessionLocal
import models
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from search_service import SearchService
import urllib.parse
from main import norm_col, norm_str

db = SessionLocal()
try:
    # Emulate the filter logic from main.py for location=["إربد", "حكما"]
    location = ["إربد", "حكما"]
    
    parent_loc = None
    target_locs = []
    
    first_loc = location[0]
    target_loc_norm = norm_str(first_loc)
    
    city = db.query(models.City).filter(norm_col(models.City.name_ar) == target_loc_norm).first()
    if city:
        parent_loc = target_loc_norm
        target_locs = location[1:]
    else:
        target_locs = location
        
    filters = []
    if parent_loc and target_locs:
        for t_loc in target_locs:
            t_loc_norm = norm_str(t_loc)
            if t_loc_norm.startswith("ال"):
                filters.append(norm_col(models.Ad.location).ilike(f"{parent_loc}, {t_loc_norm}%"))
                filters.append(norm_col(models.Ad.location).ilike(f"{parent_loc}, {t_loc_norm[2:]}%"))
            else:
                filters.append(norm_col(models.Ad.location).ilike(f"{parent_loc}, {t_loc_norm}%"))
                filters.append(norm_col(models.Ad.location).ilike(f"{parent_loc}, ال{t_loc_norm}%"))
                
    query = db.query(models.Ad)
    if filters:
        query = query.filter(or_(*filters))
        
    ads = query.all()
    with open('out_h5.txt', 'w', encoding='utf-8') as f:
        f.write(f"Ads matching filter: {len(ads)}\n")
        for ad in ads:
            f.write(f"Ad {ad.id}: {ad.location}\n")
except Exception as e:
    print('Error:', e)
finally:
    db.close()

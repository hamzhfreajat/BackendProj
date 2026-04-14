import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.sql import func, or_
from typing import List

import models
import schemas
import auth
import notifications
from notifications import send_personal_notification
from database import engine, get_db
from fb_batch_router import router as fb_batch_router
from ai_router import router as ai_router
from media_router import router as media_router
from fastapi.staticfiles import StaticFiles

import os
import json
try:
    from google import genai as _genai_new
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    _USE_NEW_SDK = False

# Fallback: hardcode the key if env var is missing
_FALLBACK_KEY = "AIzaSyDtwk07CKyqD6dnxcwBhRgf_2GbP8HHmBo"
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = _FALLBACK_KEY

app = FastAPI(title="Classifieds Backend API")

# Add CORS middleware to allow requests from the Flutter frontend and React Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, this should be restricted
    allow_credentials=False, # Must be False if allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*", "ngrok-skip-browser-warning", "Bypass-Tunnel-Reminder"],
)

app.include_router(fb_batch_router)
app.include_router(ai_router)
app.include_router(media_router)
app.include_router(auth.router)
app.include_router(notifications.router)

from verification import router as verification_router
app.include_router(verification_router)

from tracking_router import router as tracking_router
app.include_router(tracking_router)

# Mount the uploads directory to serve media files
import os
os.makedirs("uploads", exist_ok=True)
os.makedirs("static/icons", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/dashboard/metrics", response_model=schemas.UserMetrics)
def read_user_metrics(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    user = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            import jwt
            payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                user = db.query(models.User).filter(models.User.id == int(user_id)).first()
        except:
            pass

    if not user:
        return schemas.UserMetrics(id=0, user_id=0, saved_items=0, recently_viewed=0, active_ads=0)
    
    active_ads_count = db.query(models.Ad).filter(
        models.Ad.user_id == user.id,
        models.Ad.is_published == True
    ).count()

    metrics = db.query(models.UserMetric).filter(models.UserMetric.user_id == user.id).first()
    if not metrics:
        metrics = models.UserMetric(user_id=user.id, saved_items=0, recently_viewed=0, active_ads=active_ads_count)
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
    else:
        if metrics.active_ads != active_ads_count:
            metrics.active_ads = active_ads_count
            db.commit()
            db.refresh(metrics)
            
    return metrics

from sqlalchemy.orm import selectinload

@app.get("/api/locations", response_model=List[schemas.CityModel])
def read_locations(db: Session = Depends(get_db)):
    """Fetch all cities along with their sub-regions."""
    cities = db.query(models.City).options(selectinload(models.City.regions)).all()
    return cities

@app.get("/api/locations/directorates/{governorate_id}")
def get_directorates(governorate_id: int, db: Session = Depends(get_db)):
    result = db.query(models.Directorate).filter(models.Directorate.city_id == governorate_id).all()
    return [{"id": c.id, "name_ar": c.name_ar} for c in result]

@app.get("/api/locations/villages/{directorate_id}")
def get_villages(directorate_id: int, db: Session = Depends(get_db)):
    result = db.query(models.Village).filter(models.Village.directorate_id == directorate_id).all()
    return [{"id": v.id, "name_ar": v.name_ar} for v in result]

@app.get("/api/locations/basins/{village_id}")
def get_basins(village_id: int, db: Session = Depends(get_db)):
    result = db.query(models.Basin).filter(models.Basin.village_id == village_id).all()
    return [{"id": b.id, "name_ar": b.name_ar} for b in result]

@app.get("/api/locations/neighborhoods/{basin_id}")
def get_neighborhoods(basin_id: int, db: Session = Depends(get_db)):
    result = db.query(models.NeighborhoodSector).filter(models.NeighborhoodSector.basin_id == basin_id).all()
    return [{"id": n.id, "name_ar": n.name_ar} for n in result]

@app.get("/api/categories", response_model=List[schemas.Category])
def read_categories(skip: int = 0, limit: int = 20000, with_ads_only: bool = False, parent_id: str = None, location: List[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(models.Category).options(selectinload(models.Category.linked_tags)).order_by(models.Category.order_index.asc(), models.Category.id.asc())
    
    if parent_id is not None:
        if parent_id.lower() == "null" or parent_id == "0":
            query = query.filter(models.Category.parent_id == None)
        else:
            try:
                query = query.filter(models.Category.parent_id == int(parent_id))
            except ValueError:
                pass

    categories = query.offset(skip).limit(limit).all()
    
    # FAST AD COUNT INJECTION (Recursive)
    ad_query = db.query(models.Ad.category_id, func.count(models.Ad.id)).filter(models.Ad.is_published == True)
    
    if location:
        target_loc = location[-1]
        if target_loc == "محافظة العاصمة":
            target_loc = "عمان"
        elif target_loc.startswith("محافظة "):
            target_loc = target_loc.replace("محافظة ", "")
            
        filters = [models.Ad.location.ilike(f"%{target_loc}%")]
        
        city = db.query(models.City).filter(models.City.name_ar == target_loc).first()
        if city:
            for region in city.regions:
                if len(region.name_ar) > 2:
                    filters.append(models.Ad.location.ilike(f"%{region.name_ar}%"))
                    
        ad_query = ad_query.filter(or_(*filters))
        
    ad_counts = ad_query.group_by(models.Ad.category_id).all()
        
    exact_counts = {cat_id: count for cat_id, count in ad_counts}
    
    # We must construct a FULL graph to aggregate bottom-up (even if the API result is filtered)
    all_cat_relations = db.query(models.Category.id, models.Category.parent_id).all()
    children_map = {}
    for cid, pid in all_cat_relations:
        if pid:
            children_map.setdefault(pid, []).append(cid)
            
    def get_recursive_count(cid):
        total = exact_counts.get(cid, 0)
        for child_id in children_map.get(cid, []):
            total += get_recursive_count(child_id)
        return total

    counts_map = {c.id: get_recursive_count(c.id) for c in categories}
    
    if with_ads_only:
        # Pre-calculate active categories and tags using hyper-efficient mass queries
        all_cat_ids = [c.id for c in categories]
        
        # 1. Find all published ads belonging to these categories
        all_ads = db.query(models.Ad).filter(
            models.Ad.category_id.in_(all_cat_ids),
            models.Ad.is_published == True
        ).all()
        
        active_cat_ids = set([ad.category_id for ad in all_ads])
        
        # Determine parent retention - if a child is active, the parent must be kept
        retained_cat_ids = set()
        for cat in categories:
            if cat.id in active_cat_ids:
                retained_cat_ids.add(cat.id)
                if cat.parent_id:
                    retained_cat_ids.add(cat.parent_id)
        
        # 2. Extract active tags efficiently
        active_tag_ids = set()
        for ad in all_ads:
            for t in ad.linked_tags:
                active_tag_ids.add(t.id)

        # 3. Build the final filtered response from memory loops instead of sequential IO queries
        filtered = []
        for cat in categories:
            if cat.id not in retained_cat_ids:
                continue
                    
            cat_dict = {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "icon_name": cat.icon_name,
                "color_hex": cat.color_hex,
                "background_url": cat.background_url,
                "tag": cat.tag,
                "slugs": cat.slugs,
                "parent_id": cat.parent_id,
                "order_index": cat.order_index,
                "ads_count": counts_map.get(cat.id, 0),
                "linked_tags": [t for t in getattr(cat, 'linked_tags', []) if t.id in active_tag_ids]
            }
            filtered.append(cat_dict)
        return filtered
        
    for cat in categories:
        cat.ads_count = counts_map.get(cat.id, 0)
        
    return categories

@app.post("/api/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    category_data = category.model_dump(exclude={"linked_tags"})
    db_category = models.Category(**category_data)
    
    # Process Tags
    if category.linked_tags:
        for tag_name in category.linked_tags:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
            db_category.linked_tags.append(tag)
            
    # Assign it as the last item automatically
    max_index = db.query(func.max(models.Category.order_index)).scalar() or 0
    db_category.order_index = max_index + 1

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.put("/api/categories/reorder", response_model=dict)
def reorder_categories(reorder_data: List[schemas.CategoryReorder], db: Session = Depends(get_db)):
    # Bulk update method to set correct list positions efficiently
    mappings = [{"id": item.id, "order_index": item.order_index} for item in reorder_data]
    if mappings:
        db.bulk_update_mappings(models.Category, mappings)
        db.commit()
    return {"status": "success", "message": f"Successfully reordered {len(mappings)} categories"}

@app.put("/api/categories/{category_id}", response_model=schemas.Category)
def update_category(category_id: int, category_update: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    update_data = category_update.model_dump(exclude_unset=True, exclude={"linked_tags"})
    for key, value in update_data.items():
        setattr(db_category, key, value)
        
    # Process Tags update if provided
    if category_update.linked_tags is not None:
        db_category.linked_tags.clear() # Reset associations
        for tag_name in category_update.linked_tags:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
            db_category.linked_tags.append(tag)
            
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/api/categories/{category_id}", response_model=dict)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db.delete(db_category)
    db.commit()
    return {"status": "success", "message": "Category deleted successfully"}

# ============================================================
# MY ADS / SELLER DASHBOARD
# ============================================================

from datetime import datetime, timezone

def _compute_ad_status(ad: models.Ad) -> str:
    if ad.is_sold: return "Sold"
    if ad.is_rejected: return "Rejected"
    if ad.is_paused: return "Paused"
    if not ad.is_published: return "Pending"
    if ad.expires_at and ad.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc): 
        return "Expired"
    return "Active"

def _compute_performance(ad: models.Ad) -> dict:
    score = min(100, (ad.views * 0.1) + (ad.favorites_count * 2) + (ad.chats_count * 5))
    suggested = None
    if score < 20 and ad.views > 50:
        suggested = "Price might be slightly high."
    elif ad.views < 10 and ad.is_published:
        suggested = "Consider boosting for more visibility."
    elif len(ad.image_urls) < 3:
        suggested = "Add more photos to increase trust."
    return {"score": int(score), "action": suggested}

@app.get("/api/my-ads/dashboard", response_model=schemas.MyAdsDashboardSummary)
def get_my_ads_dashboard(
    current_user: models.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    ads = db.query(models.Ad).filter(models.Ad.user_id == current_user.id).all()
    
    total = len(ads)
    active = 0
    expired = 0
    pending = 0
    sold = 0
    boosted = 0
    
    views = 0
    chats = 0
    favs = 0
    
    for ad in ads:
        st = _compute_ad_status(ad)
        if st == "Active": active += 1
        elif st == "Expired": expired += 1
        elif st == "Pending": pending += 1
        elif st == "Sold": sold += 1
        
        if ad.is_boosted: boosted += 1
        
        views += getattr(ad, 'views', 0) or 0
        chats += getattr(ad, 'chats_count', 0) or 0
        favs += getattr(ad, 'favorites_count', 0) or 0
        
    return schemas.MyAdsDashboardSummary(
        totalAds=total,
        activeAds=active,
        expiredAds=expired,
        pendingAds=pending,
        soldAds=sold,
        boostedAds=boosted,
        totalViews=views,
        totalChats=chats,
        totalFavorites=favs
    )

@app.get("/api/my-ads", response_model=List[schemas.MyAdResponse])
def read_my_ads(
    status: str = "All",
    search: str = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Ad).filter(models.Ad.user_id == current_user.id)
    
    if search:
        query = query.filter(models.Ad.title.ilike(f"%{search}%"))
        
    ads = query.order_by(models.Ad.created_at.desc()).all()
    
    response_list = []
    for ad in ads:
        computed_status = _compute_ad_status(ad)
        if status != "All" and computed_status != status:
            continue
            
        perf = _compute_performance(ad)
        
        ad_resp = schemas.MyAdResponse.model_validate(ad)
        ad_resp.status = computed_status
        ad_resp.performance_score = perf["score"]
        ad_resp.suggested_action = perf["action"]
        response_list.append(ad_resp)
        
    return response_list

@app.post("/api/my-ads/bulk-action", response_model=dict)
def perform_bulk_action(
    req: schemas.BulkActionRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    ads = db.query(models.Ad).filter(models.Ad.id.in_(req.ad_ids), models.Ad.user_id == current_user.id).all()
    
    for ad in ads:
        if req.action == "delete":
            db.delete(ad)
        elif req.action == "pause":
            ad.is_paused = True
        elif req.action == "resume":
            ad.is_paused = False
        elif req.action == "sold":
            ad.is_sold = True
        elif req.action == "renew":
            ad.is_paused = False
            ad.is_sold = False
            ad.is_published = True
            # if expired_at, could extend it here
    
    db.commit()
    return {"message": f"Action '{req.action}' performed on {len(ads)} ads"}

@app.get("/api/ads", response_model=List[schemas.Ad])
def read_ads(
    skip: int = 0, 
    limit: int = 100, 
    category_id: int = None, 
    section: str = None, 
    search: str = None,
    location: List[str] = Query(None),
    min_price: float = None,
    max_price: float = None,
    is_hot: bool = None,
    is_published: bool = None,
    source_type: str = None,
    user_id: int = None,
    sort_by: str = None,
    tags: List[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Ad)
    
    if user_id is not None:
        query = query.filter(models.Ad.user_id == user_id)
        
    if search:
        query = query.filter(models.Ad.title.ilike(f"%{search}%") | models.Ad.description.ilike(f"%{search}%"))
        
    if location:
        target_loc = location[-1]
        if target_loc == "محافظة العاصمة":
            target_loc = "عمان"
        elif target_loc.startswith("محافظة "):
            target_loc = target_loc.replace("محافظة ", "")
            
        filters = [models.Ad.location.ilike(f"%{target_loc}%")]
        
        city = db.query(models.City).filter(models.City.name_ar == target_loc).first()
        if city:
            for region in city.regions:
                if len(region.name_ar) > 2:
                    filters.append(models.Ad.location.ilike(f"%{region.name_ar}%"))
                    
        query = query.filter(or_(*filters))
        
    if min_price is not None:
        query = query.filter(models.Ad.price >= min_price)
        
    if max_price is not None:
        query = query.filter(models.Ad.price <= max_price)
        
    if is_hot is not None:
        query = query.filter(models.Ad.is_hot == is_hot)
        
    if is_published is not None:
        query = query.filter(models.Ad.is_published == is_published)
        
    if source_type:
        query = query.filter(models.Ad.source_type == source_type)
        
    if tags:
        from sqlalchemy import Integer
        from collections import defaultdict
        
        grouped_tags = defaultdict(list)
        generic_tags = []
        for t in tags:
            if ":" in t:
                prefix, val = t.split(":", 1)
                grouped_tags[prefix].append(val)
            else:
                generic_tags.append(t)
                
        for prefix, values in grouped_tags.items():
            conds = []
            if prefix == "bedrooms":
                for val in values:
                    if val == '+6':
                        conds.append(models.Ad.attributes['rooms'].astext.cast(Integer) >= 6)
                    elif val == 'ستوديو':
                        conds.append(models.Ad.attributes['rooms'].astext.cast(Integer) == 0)
                    else:
                        conds.append(models.Ad.attributes['rooms'].astext.cast(Integer) == int(val))
            elif prefix == "bathrooms":
                for val in values:
                    if val == '+6':
                        conds.append(models.Ad.attributes['bathrooms'].astext.cast(Integer) >= 6)
                    else:
                        conds.append(models.Ad.attributes['bathrooms'].astext.cast(Integer) == int(val))
            elif prefix == "furnished":
                for val in values:
                    conds.append(models.Ad.attributes['furnished'].astext == val)
            elif prefix == "floor":
                for val in values:
                    conds.append(models.Ad.attributes['floor'].astext == val)
            elif prefix == "age":
                for val in values:
                    conds.append(models.Ad.attributes['building_age'].astext == val)
            elif prefix == "rent_duration":
                for val in values:
                    conds.append(models.Ad.attributes['rent_duration'].astext == val)
            elif prefix in ["land_type", "zoning_classification", "facade", "geometric_shape", "topography", "ownership_type", "is_mortgaged", "installment_possible"]:
                for val in values:
                    conds.append(models.Ad.attributes[prefix].astext == val)
            elif prefix == "available_services":
                for val in values:
                    conds.append(models.Ad.attributes['available_services'].astext.ilike(f"%{val}%"))
            elif prefix == "main_features":
                for val in values:
                    conds = [
                        models.Ad.attributes['key_features'].astext.ilike(f"%{val}%"),
                        models.Ad.attributes['building_features'].astext.ilike(f"%{val}%")
                    ]
            elif prefix == "extra_features":
                for val in values:
                    conds.append(models.Ad.attributes['building_features'].astext.ilike(f"%{val}%"))
            else:
                # Unrecognized prefix, treat as generic tags
                for val in values:
                    query = query.filter(models.Ad.linked_tags.any(models.Tag.name == f"{prefix}:{val}"))
                continue
                
            if conds:
                query = query.filter(or_(*conds))
                
        # AND logic for generic non-prefixed tags
        for t in generic_tags:
            query = query.filter(models.Ad.linked_tags.any(models.Tag.name == t))
    
    # Optional support for the old section name method (for the homepage tabs)
    if section:
        query = query.join(models.Category).filter(models.Category.name == section)
        
    # Deep nested category logic
    if category_id:
        # Get all descendant category IDs efficiently in memory
        all_cats = db.query(models.Category.id, models.Category.parent_id).all()
        cat_graph = {}
        for c_id, p_id in all_cats:
            if p_id not in cat_graph:
                cat_graph[p_id] = []
            cat_graph[p_id].append(c_id)
            
        def get_descendants_fast(cat_id):
            descendants = [cat_id]
            if cat_id in cat_graph:
                for child_id in cat_graph[cat_id]:
                    descendants.extend(get_descendants_fast(child_id))
            return descendants
            
        all_cat_ids = get_descendants_fast(category_id)
        query = query.filter(models.Ad.category_id.in_(all_cat_ids))
        
    from sqlalchemy.orm import selectinload
    query = query.options(
        selectinload(models.Ad.linked_tags),
        selectinload(models.Ad.real_estate_detail)
    )
    
    if sort_by == 'price_asc':
        query = query.order_by(models.Ad.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(models.Ad.price.desc())
    elif sort_by == 'oldest':
        query = query.order_by(models.Ad.created_at.asc())
    elif sort_by == 'most_viewed':
        query = query.order_by(models.Ad.views.desc())
    elif sort_by == 'newest':
        query = query.order_by(models.Ad.created_at.desc())
    elif sort_by == 'premium_first':
        query = query.order_by(models.Ad.is_hot.desc(), models.Ad.created_at.desc())
    elif sort_by == 'recommended' or sort_by is None:
        query = query.order_by(models.Ad.is_hot.desc(), models.Ad.views.desc(), models.Ad.created_at.desc())
    else:
        query = query.order_by(models.Ad.created_at.desc())
        
    ads = query.offset(skip).limit(limit).all()
    return ads

@app.get("/api/ads/count", response_model=dict)
def get_ads_count(
    category_id: int = None, 
    section: str = None, 
    search: str = None,
    location: List[str] = Query(None),
    min_price: float = None,
    max_price: float = None,
    is_hot: bool = None,
    is_published: bool = None,
    source_type: str = None,
    tags: List[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Ad)
    
    if search:
        query = query.filter(models.Ad.title.ilike(f"%{search}%") | models.Ad.description.ilike(f"%{search}%"))
        
    if location:
        target_loc = location[-1]
        if target_loc == "محافظة العاصمة":
            target_loc = "عمان"
        elif target_loc.startswith("محافظة "):
            target_loc = target_loc.replace("محافظة ", "")
            
        filters = [models.Ad.location.ilike(f"%{target_loc}%")]
        
        city = db.query(models.City).filter(models.City.name_ar == target_loc).first()
        if city:
            for region in city.regions:
                if len(region.name_ar) > 2:
                    filters.append(models.Ad.location.ilike(f"%{region.name_ar}%"))
                    
        query = query.filter(or_(*filters))
        
    if min_price is not None:
        query = query.filter(models.Ad.price >= min_price)
        
    if max_price is not None:
        query = query.filter(models.Ad.price <= max_price)
        
    if is_hot is not None:
        query = query.filter(models.Ad.is_hot == is_hot)
        
    if is_published is not None:
        query = query.filter(models.Ad.is_published == is_published)
        
    if source_type:
        query = query.filter(models.Ad.source_type == source_type)
        
    if tags:
        from sqlalchemy import Integer
        from collections import defaultdict
        
        grouped_tags = defaultdict(list)
        generic_tags = []
        for t in tags:
            if ":" in t:
                prefix, val = t.split(":", 1)
                grouped_tags[prefix].append(val)
            else:
                generic_tags.append(t)
                
        for prefix, values in grouped_tags.items():
            conds = []
            if prefix == "bedrooms":
                for val in values:
                    if val == '+6':
                        conds.append(models.Ad.attributes['rooms'].astext.cast(Integer) >= 6)
                    elif val == 'ستوديو':
                        conds.append(models.Ad.attributes['rooms'].astext.cast(Integer) == 0)
                    else:
                        conds.append(models.Ad.attributes['rooms'].astext.cast(Integer) == int(val))
            elif prefix == "bathrooms":
                for val in values:
                    if val == '+6':
                        conds.append(models.Ad.attributes['bathrooms'].astext.cast(Integer) >= 6)
                    else:
                        conds.append(models.Ad.attributes['bathrooms'].astext.cast(Integer) == int(val))
            elif prefix == "furnished":
                for val in values:
                    conds.append(models.Ad.attributes['furnished'].astext == val)
            elif prefix == "floor":
                for val in values:
                    conds.append(models.Ad.attributes['floor'].astext == val)
            elif prefix == "age":
                for val in values:
                    conds.append(models.Ad.attributes['building_age'].astext == val)
            elif prefix == "rent_duration":
                for val in values:
                    conds.append(models.Ad.attributes['rent_duration'].astext == val)
            elif prefix in ["land_type", "zoning_classification", "facade", "geometric_shape", "topography", "ownership_type", "is_mortgaged", "installment_possible"]:
                for val in values:
                    conds.append(models.Ad.attributes[prefix].astext == val)
            elif prefix == "available_services":
                for val in values:
                    conds.append(models.Ad.attributes['available_services'].astext.ilike(f"%{val}%"))
            elif prefix == "main_features":
                for val in values:
                    conds = [
                        models.Ad.attributes['key_features'].astext.ilike(f"%{val}%"),
                        models.Ad.attributes['building_features'].astext.ilike(f"%{val}%")
                    ]
            elif prefix == "extra_features":
                for val in values:
                    conds.append(models.Ad.attributes['building_features'].astext.ilike(f"%{val}%"))
            else:
                for val in values:
                    query = query.filter(models.Ad.linked_tags.any(models.Tag.name == f"{prefix}:{val}"))
                continue
                
            if conds:
                query = query.filter(or_(*conds))
                
        for t in generic_tags:
            query = query.filter(models.Ad.linked_tags.any(models.Tag.name == t))
    
    if section:
        query = query.join(models.Category).filter(models.Category.name == section)
        
    if category_id:
        # Get all descendant category IDs efficiently in memory
        all_cats = db.query(models.Category.id, models.Category.parent_id).all()
        cat_graph = {}
        for c_id, p_id in all_cats:
            if p_id not in cat_graph:
                cat_graph[p_id] = []
            cat_graph[p_id].append(c_id)
            
        def get_descendants_fast(cat_id):
            descendants = [cat_id]
            if cat_id in cat_graph:
                for child_id in cat_graph[cat_id]:
                    descendants.extend(get_descendants_fast(child_id))
            return descendants
            
        all_cat_ids = get_descendants_fast(category_id)
        query = query.filter(models.Ad.category_id.in_(all_cat_ids))
        
    total_count = query.count()
    return {"total_count": total_count}
@app.post("/api/ads", response_model=schemas.Ad)
def create_ad(
    ad: schemas.AdCreate, 
    background_tasks: BackgroundTasks, 
    request: Request,
    db: Session = Depends(get_db)
):
    # Determine the user ID (App users will have a token, scraper won't necessarily)
    user_id = 1 # Fallback to system/scraper user
    user_phone = ad.phone_number
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            import jwt
            payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
            token_sub = payload.get("sub")
            if token_sub:
                user_id = int(token_sub)
                
            # Grab phone number from the user object if not manually supplied
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user and not user_phone:
                user_phone = user.mobile_number
        except:
            pass # Use fallback

    ad_data = ad.model_dump()
    re_detail_data = ad_data.pop("real_estate_detail", None)
    tags_data = ad_data.pop("linked_tags", [])
    
    image_urls = ad_data.pop("image_urls", [])
    
    # We must explicitly pop phone_number and rooms to prevent SQLAlchemy from crashing as they are not columns
    ad_data.pop("phone_number", None)
    ad_data.pop("rooms", None)
    
    attributes = ad_data.get("attributes") or {}
    attributes["image_urls"] = image_urls
    if user_phone:
        attributes["phone_number"] = user_phone
        
    dynamic_data = attributes.get("dynamic_data", {})
    if dynamic_data:
        import re
        if "bedrooms" in dynamic_data:
            nums = re.findall(r'\d+', str(dynamic_data["bedrooms"]))
            if nums: attributes["rooms"] = int(nums[0])
        if "bathrooms" in dynamic_data:
            nums = re.findall(r'\d+', str(dynamic_data["bathrooms"]))
            if nums: attributes["bathrooms"] = int(nums[0])
        if "furnishing" in dynamic_data: attributes["furnished"] = dynamic_data["furnishing"]
        if "floor" in dynamic_data: attributes["floor"] = dynamic_data["floor"]
        if "age" in dynamic_data: attributes["building_age"] = dynamic_data["age"]
        if "rent_duration" in dynamic_data: attributes["rent_duration"] = dynamic_data["rent_duration"]
        if "main_features" in dynamic_data: attributes["key_features"] = dynamic_data["main_features"]
        if "extra_features" in dynamic_data: attributes["building_features"] = dynamic_data["extra_features"]
        if "nearby" in dynamic_data: attributes["nearby_places"] = dynamic_data["nearby"]
            
    ad_data["attributes"] = attributes
    
    db_ad = models.Ad(
        **ad_data,
        user_id=user_id
    )
    
    # Process Tags
    if tags_data:
        for tag_name in tags_data:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
            db_ad.linked_tags.append(tag)
            
    db.add(db_ad)
    db.commit()
    db.refresh(db_ad)
    
    # Process Real Estate Details
    if re_detail_data:
        new_re_detail = models.AdRealEstateDetail(ad_id=db_ad.id, **re_detail_data)
        db.add(new_re_detail)
        db.commit()
        db.refresh(db_ad)

    # Notify: Ad submitted confirmation to the owner
    background_tasks.add_task(
        send_personal_notification,
        target_user_id=db_ad.user_id,
        title="تم نشر إعلانك بنجاح ✅",
        body=f"إعلانك '{db_ad.title[:50]}' تم إضافته. في انتظار المراجعة.",
        notification_type="ad_created",
        reference_id=db_ad.id
    )

    return db_ad

@app.put("/api/ads/{ad_id}", response_model=schemas.Ad)
def update_ad(ad_id: int, ad_update: dict, db: Session = Depends(get_db)):
    db_ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not db_ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    re_detail_data = ad_update.pop("real_estate_detail", None)
    tags_data = ad_update.pop("linked_tags", [])
    image_urls = ad_update.pop("image_urls", [])

    ad_update.pop("phone_number", None)
    ad_update.pop("rooms", None)
    
    attributes = ad_update.get("attributes") or {}
    attributes["image_urls"] = image_urls
    
    dynamic_data = attributes.get("dynamic_data", {})
    if dynamic_data:
        import re
        if "bedrooms" in dynamic_data:
            nums = re.findall(r'\d+', str(dynamic_data["bedrooms"]))
            if nums: attributes["rooms"] = int(nums[0])
        if "bathrooms" in dynamic_data:
            nums = re.findall(r'\d+', str(dynamic_data["bathrooms"]))
            if nums: attributes["bathrooms"] = int(nums[0])
        if "furnishing" in dynamic_data: attributes["furnished"] = dynamic_data["furnishing"]
        if "floor" in dynamic_data: attributes["floor"] = dynamic_data["floor"]
        if "age" in dynamic_data: attributes["building_age"] = dynamic_data["age"]
        if "rent_duration" in dynamic_data: attributes["rent_duration"] = dynamic_data["rent_duration"]
        if "main_features" in dynamic_data: attributes["key_features"] = dynamic_data["main_features"]
        if "extra_features" in dynamic_data: attributes["building_features"] = dynamic_data["extra_features"]
        if "nearby" in dynamic_data: attributes["nearby_places"] = dynamic_data["nearby"]
            
    ad_update["attributes"] = attributes
    
    if image_urls:
        ad_update["image_url"] = image_urls[0]

    for key, value in ad_update.items():
        if hasattr(db_ad, key) and key not in ['id', 'user_id', 'created_at']:
            setattr(db_ad, key, value)
            
    # Process Tags
    if tags_data:
        db_ad.linked_tags = []
        for tag_name in tags_data:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
            db_ad.linked_tags.append(tag)

    if re_detail_data is not None:
        if db_ad.real_estate_detail:
            for r_key, r_val in re_detail_data.items():
                if hasattr(db_ad.real_estate_detail, r_key) and r_key not in ['id', 'ad_id']:
                    setattr(db_ad.real_estate_detail, r_key, r_val)
        else:
            new_re_detail = models.AdRealEstateDetail(ad_id=db_ad.id, **re_detail_data)
            db.add(new_re_detail)
            
    db.commit()
    db.refresh(db_ad)
    return db_ad

@app.put("/api/ads/{ad_id}/toggle-publish", response_model=schemas.Ad)
def toggle_publish_ad(ad_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not db_ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    db_ad.is_published = not db_ad.is_published
    db.commit()
    db.refresh(db_ad)

    # Notify: Ad publish/unpublish status change to the owner
    if db_ad.is_published:
        background_tasks.add_task(
            send_personal_notification,
            target_user_id=db_ad.user_id,
            title="إعلانك الآن مرئي للجميع 🟢",
            body=f"'{db_ad.title[:50]}' تم نشره وأصبح متاحاً للمستخدمين.",
            notification_type="ad_published",
            reference_id=db_ad.id
        )
    else:
        background_tasks.add_task(
            send_personal_notification,
            target_user_id=db_ad.user_id,
            title="تم إيقاف إعلانك 🔴",
            body=f"'{db_ad.title[:50]}' لم يعد مرئياً للمستخدمين.",
            notification_type="ad_unpublished",
            reference_id=db_ad.id
        )

    return db_ad

# ============================================================
# User-to-User Interactions & Notifications
# ============================================================

@app.post("/api/ads/{ad_id}/interaction/phone")
def notify_phone_revealed(
    ad_id: int, 
    background_tasks: BackgroundTasks, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Called when a user clicks 'Show Number' on an ad."""
    db_ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not db_ad:
        raise HTTPException(status_code=404, detail="Ad not found")
        
    # Don't notify if the user is viewing their own phone number
    if db_ad.user_id != current_user.id:
        # Prevent spamming: only send once per user per ad per hour/day (simple implementation just sends)
        background_tasks.add_task(
            notifications.send_personal_notification,
            target_user_id=db_ad.user_id,
            title="مستخدم يود التواصل معك 📞",
            body=f"قام أحدهم بإظهار رقم هاتفك في إعلان '{db_ad.title[:30]}'",
            notification_type="phone_revealed",
            reference_id=ad_id
        )
    return {"status": "success"}

@app.post("/api/ads/{ad_id}/interaction/chat")
def notify_chat_started(
    ad_id: int, 
    background_tasks: BackgroundTasks, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Called when a user clicks 'Chat' or 'WhatsApp' on an ad."""
    db_ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not db_ad:
        raise HTTPException(status_code=404, detail="Ad not found")
        
    if db_ad.user_id != current_user.id:
        background_tasks.add_task(
            notifications.send_personal_notification,
            target_user_id=db_ad.user_id,
            title="رسالة محتملة جديدة 💬",
            body=f"مستخدم مهتم بإعلانك '{db_ad.title[:30]}' وانتقل للمحادثة.",
            notification_type="chat_started",
            reference_id=ad_id
        )
    return {"status": "success"}

from sqlalchemy.dialects.postgresql import insert as pg_insert

@app.post("/api/ads/{ad_id}/interaction/view")
def record_ad_view(
    ad_id: int, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Logs an ad view per user for the history tracking."""
    # Ensure ad exists
    db_ad = db.query(models.Ad).filter(models.Ad.id == ad_id).first()
    if not db_ad:
        raise HTTPException(status_code=404, detail="Ad not found")

    # Use raw insert / update on conflict for tracking view_at
    stmt = pg_insert(models.user_viewed_ads).values(
        user_id=current_user.id,
        ad_id=ad_id,
        viewed_at=func.now()
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id', 'ad_id'],
        set_=dict(viewed_at=func.now())
    )
    db.execute(stmt)
    db.commit()
    
    return {"status": "success"}

@app.get("/api/my-ads/recently-viewed", response_model=List[schemas.Ad])
def read_recently_viewed_ads(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch the latest 20 ads viewed chronologically by the user."""
    # Join Ads with user_viewed_ads, sort by viewed_at DESC
    from sqlalchemy.orm import selectinload
    
    query = db.query(models.Ad).join(
        models.user_viewed_ads, 
        models.Ad.id == models.user_viewed_ads.c.ad_id
    ).filter(
        models.user_viewed_ads.c.user_id == current_user.id
    ).order_by(
        models.user_viewed_ads.c.viewed_at.desc()
    ).options(
        selectinload(models.Ad.linked_tags),
        selectinload(models.Ad.real_estate_detail)
    ).limit(20)

    return query.all()

from sqlalchemy.orm import Session, joinedload

@app.get("/api/ticker", response_model=List[schemas.LiveTicker])
def read_ticker(db: Session = Depends(get_db)):
    # Fetch latest 5 ticker messages
    tickers = db.query(models.LiveTicker).order_by(models.LiveTicker.created_at.desc()).limit(5).all()
    return tickers

@app.get("/api/stories", response_model=List[schemas.Story])
def read_stories(db: Session = Depends(get_db)):
    stories = db.query(models.Story).options(joinedload(models.Story.owner)).order_by(models.Story.created_at.desc()).limit(20).all()
    return stories


# --- Saved Groups Admin API ---

@app.get("/api/saved-groups", response_model=List[schemas.SavedGroup])
def read_saved_groups(db: Session = Depends(get_db)):
    return db.query(models.SavedGroup).all()

@app.post("/api/saved-groups", response_model=schemas.SavedGroup)
def create_saved_group(group: schemas.SavedGroupCreate, db: Session = Depends(get_db)):
    db_group = models.SavedGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.delete("/api/saved-groups/{group_id}")
def delete_saved_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(models.SavedGroup).filter(models.SavedGroup.id == group_id).first()
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"message": "Deleted successfully"}

@app.get("/api/users/me/profile", response_model=schemas.User)
def get_my_profile(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return current_user

@app.patch("/api/users/me/profile", response_model=schemas.User)
def update_my_profile(update_data: schemas.UserUpdate, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if update_data.username is not None:
        current_user.username = update_data.username
    if update_data.bio is not None:
        current_user.bio = update_data.bio
    if update_data.preferred_contact is not None:
        current_user.preferred_contact = update_data.preferred_contact
    if update_data.languages_spoken is not None:
        current_user.languages_spoken = update_data.languages_spoken
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url
    if update_data.cover_image_url is not None:
        current_user.cover_image_url = update_data.cover_image_url
    if update_data.user_type is not None:
        current_user.user_type = update_data.user_type
        
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/api/users/{user_id}/profile", response_model=schemas.User)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/api/users/{user_id}/reviews", response_model=List[schemas.UserReview])
def get_user_reviews(user_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.UserReview).filter(models.UserReview.target_user_id == user_id).all()
    return reviews


@app.on_event("startup")
async def startup_event():
    print("INFO: Background periodic scraper is disabled (using extension instead).")
    # asyncio.create_task(scraper.run_periodic_scraper())

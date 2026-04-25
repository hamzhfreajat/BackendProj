from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import json

from database import get_db
import models
import schemas
import jwt
from auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/tracking", tags=["Tracking & Dashboard"])

def get_optional_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return db.query(models.User).filter(models.User.id == int(user_id)).first()
    except Exception:
        pass
    return None

@router.post("/log_event", response_model=schemas.UserActivityLogOut)
def log_user_event(
    req: schemas.LogEventRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_optional_user)
):
    try:
        user_id = current_user.id if current_user else None
        log = models.UserActivityLog(
            user_id=user_id,
            action_type=req.action_type,
            category_id=req.category_id,
            filters_json=req.filters_json,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights", response_model=schemas.DashboardInsightsOut)
def get_dashboard_insights(db: Session = Depends(get_db)):
    # 1. Total Logs
    total_logs = db.query(models.UserActivityLog).count()
    
    # 2. Top Categories (Heatmap)
    top_cats = db.query(
        models.UserActivityLog.category_id, 
        models.Category.name,
        func.count(models.UserActivityLog.id).label('count')
    ).join(models.Category, models.UserActivityLog.category_id == models.Category.id)\
     .group_by(models.UserActivityLog.category_id, models.Category.name)\
     .order_by(func.count(models.UserActivityLog.id).desc())\
     .limit(10).all()
     
    top_categories = [{"category_id": r[0], "name": r[1], "count": r[2]} for r in top_cats]
    
    # 3. Recent Activity (Feed)
    recent = db.query(models.UserActivityLog)\
        .order_by(models.UserActivityLog.created_at.desc())\
        .limit(20).all()
        
    recent_activity = []
    for r in recent:
        username = r.user.username if r.user else "Guest"
        cat_name = r.category.name if r.category else "None"
        recent_activity.append({
            "id": r.id,
            "username": username,
            "action": r.action_type,
            "category": cat_name,
            "filters": r.filters_json,
            "time": r.created_at.isoformat()
        })
        
    # 4. Filter Analytics
    # Count how many times filters are applied
    filter_logs = db.query(models.UserActivityLog).filter(models.UserActivityLog.action_type == "APPLY_FILTER").all()
    filter_analytics = []
    # simple aggregation
    for f in filter_logs:
        if f.filters_json:
           filter_analytics.append(f.filters_json)
           
    # 5. Location Stats
    # Ensure all static cities and regions exist so 0-count regions are shown
    all_cities = db.query(models.City).all()
    all_regions = db.query(models.Region).all()
    
    location_breakdown = {}
    city_map = {}
    
    for c in all_cities:
        city_map[c.id] = c.name_ar
        location_breakdown[c.name_ar] = {"total": 0, "regions": {}}
        
    for r in all_regions:
        if r.city_id in city_map:
            c_name = city_map[r.city_id]
            location_breakdown[c_name]["regions"][r.name_ar] = 0

    loc_stats_query = db.query(
        models.Ad.location,
        func.count(models.Ad.id).label('count')
    ).group_by(models.Ad.location).order_by(func.count(models.Ad.id).desc()).all()
    
    for loc_str, count in loc_stats_query:
        if not loc_str:
            continue
        parts = [p.strip() for p in loc_str.split(',')]
        if not parts:
            continue
            
        city_name = parts[0]
        region_name = parts[1] if len(parts) > 1 else 'أخرى'
        
        if city_name not in location_breakdown:
            location_breakdown[city_name] = {"total": 0, "regions": {}}
            
        location_breakdown[city_name]["total"] += count
        
        if region_name not in location_breakdown[city_name]["regions"]:
            location_breakdown[city_name]["regions"][region_name] = 0
            
        location_breakdown[city_name]["regions"][region_name] += count
        
    location_stats_list = []
    for city, data in location_breakdown.items():
        regions_list = [{"name": r_name, "count": r_count} for r_name, r_count in data["regions"].items()]
        regions_list.sort(key=lambda x: x["count"], reverse=True)
        location_stats_list.append({
            "city": city,
            "total_ads": data["total"],
            "regions": regions_list
        })
        
    location_stats_list.sort(key=lambda x: x["total_ads"], reverse=True)

    # 6. Real Estate Category Stats
    roots_to_track = [3, 2, 10313] # عقارات للإيجار, عقارات للبيع, أراضي (by user request)
    
    all_cats_query = db.query(
        models.Category.id,
        models.Category.name,
        models.Category.parent_id,
        func.count(models.Ad.id).label('count')
    ).outerjoin(models.Ad, models.Category.id == models.Ad.category_id).group_by(models.Category.id).all()
    
    cat_dict = {}
    for row in all_cats_query:
        cat_dict[row.id] = {
            "name": row.name,
            "parent_id": row.parent_id,
            "count": row.count,
        }
        
    def get_subtree_sum(node_id, visited=None):
        if visited is None: visited = set()
        if node_id in visited: return 0
        visited.add(node_id)
        if node_id not in cat_dict: return 0
        total = cat_dict[node_id]['count']
        for child_id, child_data in cat_dict.items():
            if child_data['parent_id'] == node_id:
                total += get_subtree_sum(child_id, visited)
        return total

    real_estate_stats = []
    
    for root_id in roots_to_track:
        if root_id in cat_dict:
            root_data = cat_dict[root_id]
            children_list = []
            root_total = root_data['count'] 
            
            for cid, cdata in cat_dict.items():
                if cdata['parent_id'] == root_id:
                    c_sum = get_subtree_sum(cid)
                    root_total += c_sum
                    children_list.append({
                        "name": cdata['name'],
                        "count": c_sum
                    })
                    
            # Sort children by count descending
            children_list.sort(key=lambda x: x["count"], reverse=True)
            
            # Use specific "الأراضي" label if it's the id 10313 root
            display_name = "الأراضي" if root_id == 10313 else root_data['name']
            
            real_estate_stats.append({
                "name": display_name,
                "total_count": root_total,
                "children": children_list
            })
           
    return {
        "total_logs": total_logs,
        "top_categories": top_categories,
        "recent_activity": recent_activity,
        "filter_analytics": filter_analytics[:50], # return top 50 for insights
        "location_stats": location_stats_list,
        "real_estate_stats": real_estate_stats
    }

@router.get("/personalized_ads", response_model=List[schemas.PersonalizedAdsOut])
def get_personalized_ads(db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_optional_user)):
    target_category_id = None
    target_category_name = None
    
    # 1. Try to find the user's most interacted category
    if current_user:
        top_cat = db.query(models.UserActivityLog.category_id, func.count(models.UserActivityLog.id).label('c'))\
            .filter(models.UserActivityLog.user_id == current_user.id)\
            .filter(models.UserActivityLog.category_id.isnot(None))\
            .group_by(models.UserActivityLog.category_id)\
            .order_by(func.count(models.UserActivityLog.id).desc())\
            .first()
            
        if top_cat:
            target_category_id = top_cat[0]
            cat_obj = db.query(models.Category).filter(models.Category.id == target_category_id).first()
            if cat_obj:
                target_category_name = cat_obj.name

    # 2. If no user data or guest, just pick a trending category from global tracking
    if not target_category_id:
        top_global = db.query(models.UserActivityLog.category_id, func.count(models.UserActivityLog.id).label('c'))\
            .filter(models.UserActivityLog.category_id.isnot(None))\
            .group_by(models.UserActivityLog.category_id)\
            .order_by(func.count(models.UserActivityLog.id).desc())\
            .first()
        if top_global:
            target_category_id = top_global[0]
            cat_obj = db.query(models.Category).filter(models.Category.id == target_category_id).first()
            if cat_obj:
                target_category_name = cat_obj.name
                
    # 3. Fallback to generic "عقارات للبيع" (ID: 2) if nothing is tracked yet
    if not target_category_id:
        target_category_id = 2
        target_category_name = "عقارات للبيع"
        
    # 4. Fetch the highest matched ads!
    ads = db.query(models.Ad)\
        .filter(models.Ad.category_id == target_category_id)\
        .order_by(models.Ad.created_at.desc())\
        .limit(10).all()
        
    title_text = f"أكمل تصفح {target_category_name}" if target_category_name else "قد يعجبك أيضاً"
    
    # Extract latest filters for this category
    latest_filters = None
    if current_user:
        last_log = db.query(models.UserActivityLog).filter(
            models.UserActivityLog.user_id == current_user.id,
            models.UserActivityLog.category_id == target_category_id,
            models.UserActivityLog.filters_json.isnot(None)
        ).order_by(models.UserActivityLog.created_at.desc()).first()
        if last_log:
            latest_filters = last_log.filters_json
    
    lanes = []
    lanes.append({
        "title": title_text,
        "category_id": target_category_id,
        "ads": ads,
        "filters_json": latest_filters
    })
    
    # Smart Secondary Lanes
    if latest_filters and target_category_name:
        # A. Location Based
        if 'locations' in latest_filters and latest_filters['locations']:
            loc = latest_filters['locations'][0]
            loc_title = f"{target_category_name} في {loc}"
            loc_ads = db.query(models.Ad)\
                .filter(models.Ad.category_id == target_category_id)\
                .filter(models.Ad.location.contains(loc))\
                .order_by(models.Ad.created_at.desc())\
                .limit(10).all()
            if loc_ads:
                lanes.append({
                    "title": loc_title,
                    "category_id": target_category_id,
                    "ads": loc_ads,
                    "filters_json": {"locations": [loc]}
                })
        
        # B. Tags Based (e.g., Furnished or Specific Spec)
        if 'tags' in latest_filters and latest_filters['tags']:
            # Pick the first meaningful tag
            for tag in latest_filters['tags']:
                tag_title = f"{target_category_name} {tag}"
                # Simplistic search utilizing JSON attributes or description matching
                # Since structured tags are often in descriptions or titles:
                tag_ads = db.query(models.Ad)\
                    .filter(models.Ad.category_id == target_category_id)\
                    .filter(models.Ad.title.contains(tag) | models.Ad.raw_description.contains(tag))\
                    .order_by(models.Ad.created_at.desc())\
                    .limit(10).all()
                if tag_ads:
                    lanes.append({
                        "title": tag_title,
                        "category_id": target_category_id,
                        "ads": tag_ads,
                        "filters_json": {"tags": [tag]}
                    })
                break

    return lanes

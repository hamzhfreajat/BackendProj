from fastapi import APIRouter, Request, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

class TelemetryEventPayload(BaseModel):
    event_name: str
    user_id: Optional[str] = None
    screen: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

class TelemetryBatchPayload(BaseModel):
    events: List[TelemetryEventPayload]

@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry_batch(payload: TelemetryBatchPayload, request: Request):
    """
    Ingest a batch of telemetry events and queue them for processing.
    """
    arq_pool = getattr(request.app.state, 'arq_pool', None)
    if not arq_pool:
        # Fallback if ARQ is not running or not configured
        raise HTTPException(status_code=503, detail="Task queue unavailable")
    
    # Extract IP address
    ip_address = request.headers.get('x-forwarded-for') or request.client.host
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    # Convert Pydantic payload to dicts for ARQ
    events_list = []
    for event in payload.events:
        event_dict = event.dict()
        event_dict['ip_address'] = ip_address
        events_list.append(event_dict)
    
    # Enqueue job
    await arq_pool.enqueue_job('process_telemetry_batch', events_list)
    
    return {"status": "accepted"}

@router.get("/errors")
def get_errors(db: Session = Depends(get_db)):
    """
    Get recent error logs for the admin dashboard.
    """
    query = text("""
        SELECT 
            t.id, 
            t.timestamp, 
            t.user_id, 
            u.full_name, 
            u.phone,
            t.metadata_json
        FROM telemetry_events t
        LEFT JOIN users u ON u.id::varchar = t.user_id
        WHERE t.event_name = 'error'
        ORDER BY t.timestamp DESC
        LIMIT 100;
    """)
    result = db.execute(query).fetchall()
    
    errors = []
    for row in result:
        meta = row.metadata_json or {}
        errors.append({
            "id": row.id,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "user_id": row.user_id,
            "user_name": row.full_name,
            "user_phone": row.phone,
            "screen_name": meta.get("screen_name", "Unknown"),
            "error_message": meta.get("error_message", "Unknown Error"),
            "stack_trace": meta.get("stack_trace", "")
        })
    
    return errors

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """
    Get analytics for the admin dashboard.
    Includes DAU, top screens, and user journey funnel.
    """
    # Daily Active Users (DAU) last 30 days
    dau_query = text('''
        SELECT DATE(timestamp) as day, COUNT(DISTINCT user_id) as active_users
        FROM telemetry_events
        WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
        AND user_id IS NOT NULL
        GROUP BY day 
        ORDER BY day ASC;
    ''')
    dau_results = db.execute(dau_query).fetchall()
    dau_data = [{"day": str(r.day), "active_users": r.active_users} for r in dau_results]

    # Top Visited Screens
    screens_query = text('''
        SELECT metadata_json->>'screen_name' as screen, COUNT(*) as views
        FROM telemetry_events
        WHERE event_name = 'screen_viewed' AND metadata_json->>'screen_name' IS NOT NULL
        GROUP BY metadata_json->>'screen_name'
        ORDER BY views DESC 
        LIMIT 50;
    ''')
    screens_results = db.execute(screens_query).fetchall()
    top_screens = [{"screen": r.screen, "views": r.views} for r in screens_results]

    # Funnel: category_viewed -> property_viewed -> contact_agent_initiated
    funnel_query = text('''
        SELECT
          COUNT(DISTINCT CASE WHEN event_name = 'category_viewed' THEN user_id END) AS step1,
          COUNT(DISTINCT CASE WHEN event_name = 'property_viewed' THEN user_id END) AS step2,
          COUNT(DISTINCT CASE WHEN event_name = 'contact_agent_initiated' THEN user_id END) AS step3
        FROM telemetry_events
        WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
    ''')
    funnel_result = db.execute(funnel_query).fetchone()
    
    funnel_data = [
        {"name": "Categories", "value": funnel_result.step1 if funnel_result else 0},
        {"name": "Properties", "value": funnel_result.step2 if funnel_result else 0},
        {"name": "Contacts", "value": funnel_result.step3 if funnel_result else 0},
    ]

    # Sankey User Flow
    sankey_query = text('''
        SELECT 
          metadata_json->>'previous_screen' as source_screen,
          metadata_json->>'screen_name' as target_screen,
          COUNT(*) as value
        FROM telemetry_events
        WHERE event_name = 'screen_viewed'
          AND metadata_json->>'previous_screen' IS NOT NULL
          AND metadata_json->>'screen_name' IS NOT NULL
        GROUP BY source_screen, target_screen
        HAVING COUNT(*) > 0
        ORDER BY value DESC
        LIMIT 500;
    ''')
    sankey_results = db.execute(sankey_query).fetchall()
    
    nodes_dict = {}
    links = []
    for r in sankey_results:
        src = r.source_screen
        tgt = r.target_screen
        val = r.value
        
        # Filter out self-loops to make sankey cleaner
        if src == tgt:
            continue
            
        if src not in nodes_dict:
            nodes_dict[src] = len(nodes_dict)
        if tgt not in nodes_dict:
            nodes_dict[tgt] = len(nodes_dict)
            
        links.append({
            "source": nodes_dict[src],
            "target": nodes_dict[tgt],
            "value": val
        })
        
    nodes = [{"name": name} for name in nodes_dict.keys()]
    sankey_data = {"nodes": nodes, "links": links}

    # Friction Metrics
    # Rage Taps
    rage_taps_query = text('''
        SELECT 
          screen,
          metadata_json->>'location' as location,
          metadata_json->>'target_name' as target
        FROM telemetry_events
        WHERE event_name = 'rage_tap'
          AND metadata_json->>'location' IS NOT NULL
          AND screen IS NOT NULL 
          AND screen != ''
        LIMIT 500;
    ''')
    rage_taps_results = db.execute(rage_taps_query).fetchall()
    
    rage_taps_data = []
    for r in rage_taps_results:
        try:
            x_str, y_str = r.location.split(',')
            rage_taps_data.append({
                "screen": r.screen,
                "x": float(x_str.strip()),
                "y": float(y_str.strip()),
                "target": r.target
            })
        except:
            continue

    # Dead Clicks
    dead_clicks_query = text('''
        SELECT 
          screen,
          metadata_json->>'x_pos' as x,
          metadata_json->>'y_pos' as y
        FROM telemetry_events
        WHERE event_name = 'dead_click'
          AND metadata_json->>'x_pos' IS NOT NULL
          AND screen IS NOT NULL 
          AND screen != ''
        LIMIT 500;
    ''')
    dead_clicks_results = db.execute(dead_clicks_query).fetchall()
    
    dead_clicks_data = []
    for r in dead_clicks_results:
        try:
            dead_clicks_data.append({
                "screen": r.screen,
                "x": float(r.x),
                "y": float(r.y)
            })
        except:
            continue

    # Form Abandonment
    form_abandoned_query = text('''
        SELECT 
          metadata_json->>'form_name' as form,
          metadata_json->>'last_active_field' as field,
          COUNT(*) as count
        FROM telemetry_events
        WHERE event_name = 'form_abandoned'
        GROUP BY 1, 2
        ORDER BY count DESC LIMIT 50;
    ''')
    form_abandoned_results = db.execute(form_abandoned_query).fetchall()
    form_abandoned_data = [{"form_field": f"{r.form} ({r.field})", "count": r.count} for r in form_abandoned_results]

    # U-Turns
    u_turns_query = text('''
        SELECT 
          COALESCE(screen, 'Unknown') as screen,
          COUNT(*) as count
        FROM telemetry_events
        WHERE event_name = 'u_turn'
        GROUP BY 1
        ORDER BY count DESC LIMIT 50;
    ''')
    u_turns_results = db.execute(u_turns_query).fetchall()
    u_turns_data = [{"screen": r.screen, "count": r.count} for r in u_turns_results]
    
    friction_metrics = {
        "rage_taps": rage_taps_data,
        "dead_clicks": dead_clicks_data,
        "form_abandonment": form_abandoned_data,
        "u_turns": u_turns_data
    }

    return {
        "dau": dau_data,
        "top_screens": top_screens,
        "funnel": funnel_data,
        "sankey": sankey_data,
        "friction_metrics": friction_metrics
    }

@router.get("/advanced-analytics")
def get_advanced_analytics(db: Session = Depends(get_db)):
    """
    Get 100% real advanced SaaS and Category analytics from the database.
    """
    # ---- USERS ANALYTICS ----
    total_users_query = text("SELECT COUNT(*) FROM users;")
    total_users = db.execute(total_users_query).scalar() or 0

    dau_query = text("SELECT COUNT(DISTINCT user_id) FROM telemetry_events WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' AND user_id IS NOT NULL;")
    dau = db.execute(dau_query).scalar() or 0

    mau_query = text("SELECT COUNT(DISTINCT user_id) FROM telemetry_events WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days' AND user_id IS NOT NULL;")
    mau = db.execute(mau_query).scalar() or 0

    stickiness = round((dau / mau * 100), 1) if mau > 0 else 0

    # User Growth Rate
    growth_query = text("""
        WITH this_month AS (SELECT count(*) as cnt FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'),
             last_month AS (SELECT count(*) as cnt FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '60 days' AND created_at < CURRENT_DATE - INTERVAL '30 days')
        SELECT this_month.cnt as this, last_month.cnt as last FROM this_month, last_month;
    """)
    growth_res = db.execute(growth_query).fetchone()
    growth_this = growth_res.this if growth_res else 0
    growth_last = growth_res.last if growth_res else 1
    growth_rate = round(((growth_this - growth_last) / max(growth_last, 1)) * 100, 1)
    growth_str = f"+{growth_rate}%" if growth_rate > 0 else f"{growth_rate}%"

    # Time to Value (TTV)
    ttv_query = text("""
        SELECT AVG(EXTRACT(EPOCH FROM (first_ad.created_at - u.created_at))) / 86400 as avg_days
        FROM users u
        JOIN (SELECT user_id, MIN(created_at) as created_at FROM ads GROUP BY user_id) first_ad ON u.id = first_ad.user_id;
    """)
    ttv_res = db.execute(ttv_query).scalar()
    ttv_str = f"{round(ttv_res, 1)} أيام" if ttv_res else "غير متاح"

    # Active Users History
    au_query = text("""
        SELECT to_char(DATE_TRUNC('month', timestamp), 'Mon YYYY') as month, 
               COUNT(DISTINCT user_id) as mau,
               COUNT(DISTINCT user_id) / 30 as avg_dau
        FROM telemetry_events 
        WHERE timestamp >= CURRENT_DATE - INTERVAL '6 months' 
        GROUP BY DATE_TRUNC('month', timestamp), month 
        ORDER BY DATE_TRUNC('month', timestamp) ASC;
    """)
    au_res = db.execute(au_query).fetchall()
    au_categories = [r.month for r in au_res]
    au_mau = [r.mau for r in au_res]
    au_dau = [int(r.avg_dau) for r in au_res]

    # Onboarding Funnel (Real)
    funnel_users = total_users
    funnel_active = db.execute(text("SELECT count(distinct user_id) FROM telemetry_events WHERE user_id IS NOT NULL;")).scalar() or 0
    funnel_searched = db.execute(text("SELECT count(distinct user_id) FROM telemetry_events WHERE event_name = 'search';")).scalar() or 0
    funnel_posted = db.execute(text("SELECT count(distinct user_id) FROM ads;")).scalar() or 0
    f1 = 100
    f2 = round((funnel_active / max(funnel_users, 1) * 100))
    f3 = round((funnel_searched / max(funnel_users, 1) * 100))
    f4 = round((funnel_posted / max(funnel_users, 1) * 100))

    # Geographic Distribution (Real)
    geo_query = text("""
        SELECT 
          CASE 
            WHEN phone LIKE '07%' THEN 'الأردن' 
            WHEN phone LIKE '+966%' THEN 'السعودية'
            WHEN phone LIKE '+971%' THEN 'الإمارات'
            WHEN phone LIKE '+20%' THEN 'مصر'
            ELSE 'أخرى' 
          END as country, 
          COUNT(*) as cnt
        FROM users 
        WHERE phone IS NOT NULL
        GROUP BY country
        ORDER BY cnt DESC;
    """)
    geo_res = db.execute(geo_query).fetchall()
    geo_labels = [r.country for r in geo_res]
    geo_data = [r.cnt for r in geo_res]

    # ---- CATEGORY ANALYTICS ----
    total_categories_query = text("SELECT COUNT(*) FROM categories;")
    total_categories = db.execute(total_categories_query).scalar() or 0

    active_categories_query = text("SELECT COUNT(DISTINCT category_id) FROM ads WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';")
    active_categories = db.execute(active_categories_query).scalar() or 0

    total_classifications_query = text("SELECT COUNT(*) FROM ai_training_logs;")
    total_classifications = db.execute(total_classifications_query).scalar() or 0

    failed_classifications_query = text("SELECT COUNT(*) FROM ai_training_logs WHERE status != 'success';")
    failed_classifications = db.execute(failed_classifications_query).scalar() or 0
    failed_rate = round((failed_classifications / max(total_classifications, 1) * 100), 1)

    # Classification Volume by Category
    vol_query = text("""
        SELECT ai_output->>'category_id' as cat_id, COUNT(*) as vol 
        FROM ai_training_logs 
        WHERE ai_output->>'category_id' IS NOT NULL 
        GROUP BY cat_id 
        ORDER BY vol DESC 
        LIMIT 10;
    """)
    vol_results = db.execute(vol_query).fetchall()
    
    cat_names_query = text("SELECT id, name FROM categories;")
    cat_names = {str(r.id): r.name for r in db.execute(cat_names_query).fetchall()}

    classification_volume = []
    for r in vol_results:
        cat_id_str = str(r.cat_id)
        if cat_id_str.endswith(".0"): cat_id_str = cat_id_str[:-2]
        classification_volume.append({
            "category": cat_names.get(cat_id_str, f"Category {cat_id_str}"),
            "volume": r.vol
        })

    # AI Classification Trend (Last 7 Days)
    trend_query = text("""
        SELECT to_char(DATE(created_at), 'Dy') as day, COUNT(*) as vol 
        FROM ai_training_logs 
        WHERE created_at >= CURRENT_DATE - INTERVAL '6 days' 
        GROUP BY DATE(created_at), day 
        ORDER BY DATE(created_at) ASC;
    """)
    trend_res = db.execute(trend_query).fetchall()
    trend_categories = [r.day for r in trend_res]
    trend_data = [r.vol for r in trend_res]

    return {
        "users": {
            "total_users": total_users,
            "dau": dau,
            "mau": mau,
            "stickiness": stickiness,
            "growth_rate": growth_str,
            "ttv": ttv_str,
            "total_ads_posted": funnel_posted,
            "charts": {
                "active_users": {
                    "categories": au_categories,
                    "mau": au_mau,
                    "dau": au_dau
                },
                "funnel": [f1, f2, f3, f4],
                "geo": {
                    "labels": geo_labels,
                    "data": geo_data
                }
            }
        },
        "categories": {
            "total_categories": total_categories,
            "active_categories": active_categories,
            "total_classifications": total_classifications,
            "failed_rate": failed_rate,
            "classification_volume": classification_volume,
            "charts": {
                "trend": {
                    "categories": trend_categories,
                    "data": trend_data
                }
            }
        }
    }


@router.get("/user-sankey")
def get_user_sankey(email: str, db: Session = Depends(get_db)):
    # 1. Lookup user by email
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_id_str = str(user.id)
    
    # 2. Query telemetry events for this user_id
    sankey_query = text('''
        SELECT 
          metadata_json->>'previous_screen' as source_screen,
          metadata_json->>'screen_name' as target_screen,
          COUNT(*) as value
        FROM telemetry_events
        WHERE event_name = 'screen_viewed'
          AND metadata_json->>'previous_screen' IS NOT NULL
          AND metadata_json->>'screen_name' IS NOT NULL
          AND user_id = :uid
        GROUP BY source_screen, target_screen
        HAVING COUNT(*) > 0
        ORDER BY value DESC
        LIMIT 500;
    ''')
    
    results = db.execute(sankey_query, {"uid": user_id_str}).fetchall()
    
    nodes_dict = {}
    links = []
    for r in results:
        src = r.source_screen
        tgt = r.target_screen
        val = r.value
        
        if src == tgt:
            continue
            
        if src not in nodes_dict:
            nodes_dict[src] = len(nodes_dict)
        if tgt not in nodes_dict:
            nodes_dict[tgt] = len(nodes_dict)
            
        links.append({
            "source": nodes_dict[src],
            "target": nodes_dict[tgt],
            "value": val
        })
        
    nodes = [{"name": name} for name in nodes_dict.keys()]
    
    return {
        "user_id": user.id,
        "email": user.email,
        "sankey": {
            "nodes": nodes,
            "links": links
        }
    }


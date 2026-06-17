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
    
    # Convert Pydantic payload to dicts for ARQ
    events_list = [event.dict() for event in payload.events]
    
    # Enqueue job
    await arq_pool.enqueue_job('process_telemetry_batch', events_list)
    
    return {"status": "accepted"}

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
        LIMIT 10;
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
        LIMIT 50;
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
          metadata_json->>'location' as location,
          metadata_json->>'target_name' as target,
          COUNT(*) as count
        FROM telemetry_events
        WHERE event_name = 'rage_tap'
        GROUP BY 1, 2
        ORDER BY count DESC LIMIT 10;
    ''')
    rage_taps_results = db.execute(rage_taps_query).fetchall()
    rage_taps_data = [{"location": f"{r.location} - {r.target}", "count": r.count} for r in rage_taps_results]

    # Dead Clicks
    dead_clicks_query = text('''
        SELECT 
          COALESCE(screen, 'Unknown') as screen,
          COUNT(*) as count
        FROM telemetry_events
        WHERE event_name = 'dead_click'
        GROUP BY 1
        ORDER BY count DESC LIMIT 10;
    ''')
    dead_clicks_results = db.execute(dead_clicks_query).fetchall()
    dead_clicks_data = [{"screen": r.screen, "count": r.count} for r in dead_clicks_results]

    # Form Abandonment
    form_abandoned_query = text('''
        SELECT 
          metadata_json->>'form_name' as form,
          metadata_json->>'last_active_field' as field,
          COUNT(*) as count
        FROM telemetry_events
        WHERE event_name = 'form_abandoned'
        GROUP BY 1, 2
        ORDER BY count DESC LIMIT 10;
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
        ORDER BY count DESC LIMIT 10;
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

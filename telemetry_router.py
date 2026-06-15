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

    return {
        "dau": dau_data,
        "top_screens": top_screens,
        "funnel": funnel_data
    }

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
        SELECT screen, COUNT(*) as views
        FROM telemetry_events
        WHERE event_name = 'screen_view' AND screen IS NOT NULL
        GROUP BY screen 
        ORDER BY views DESC 
        LIMIT 10;
    ''')
    screens_results = db.execute(screens_query).fetchall()
    top_screens = [{"screen": r.screen, "views": r.views} for r in screens_results]

    # Funnel: view_home -> view_cart -> checkout_success
    funnel_query = text('''
        SELECT
          COUNT(DISTINCT CASE WHEN event_name = 'view_home' THEN user_id END) AS step1_home,
          COUNT(DISTINCT CASE WHEN event_name = 'view_cart' THEN user_id END) AS step2_cart,
          COUNT(DISTINCT CASE WHEN event_name = 'checkout_success' THEN user_id END) AS step3_checkout
        FROM telemetry_events
        WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
    ''')
    funnel_result = db.execute(funnel_query).fetchone()
    
    funnel_data = [
        {"name": "Home", "value": funnel_result.step1_home if funnel_result else 0},
        {"name": "Cart", "value": funnel_result.step2_cart if funnel_result else 0},
        {"name": "Checkout", "value": funnel_result.step3_checkout if funnel_result else 0},
    ]

    return {
        "dau": dau_data,
        "top_screens": top_screens,
        "funnel": funnel_data
    }

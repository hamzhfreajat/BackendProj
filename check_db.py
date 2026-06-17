import sys
import os
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
res = db.execute(text("SELECT metadata_json->>'previous_screen' as source, metadata_json->>'screen_name' as target, COUNT(*) as c FROM telemetry_events WHERE event_name = 'screen_viewed' GROUP BY source, target;")).fetchall()

for row in res:
    print(f"source: {row.source}, target: {row.target}, count: {row.c}")

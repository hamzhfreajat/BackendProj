import sys
import os
sys.path.append(os.getcwd())
import json
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    res = conn.execute(text("SELECT metadata_json FROM telemetry_events WHERE event_name = 'error' ORDER BY timestamp DESC LIMIT 20")).fetchall()
    for row in res:
        print(json.dumps(row[0], indent=2, ensure_ascii=False))

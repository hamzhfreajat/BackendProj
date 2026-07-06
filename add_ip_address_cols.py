import sys
import os
sys.path.append(os.getcwd())
from database import engine
from sqlalchemy import text

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN ip_address VARCHAR(50);"))
        print("Added ip_address to users")
    except Exception as e:
        print("users:", e)
    try:
        conn.execute(text("ALTER TABLE ads ADD COLUMN ip_address VARCHAR(50);"))
        print("Added ip_address to ads")
    except Exception as e:
        print("ads:", e)
    try:
        conn.execute(text("ALTER TABLE telemetry_events ADD COLUMN ip_address VARCHAR(50);"))
        print("Added ip_address to telemetry_events")
    except Exception as e:
        print("telemetry_events:", e)

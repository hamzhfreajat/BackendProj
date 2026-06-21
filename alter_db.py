from sqlalchemy import text
from database import engine

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE saved_filters ADD COLUMN IF NOT EXISTS match_count INTEGER DEFAULT 0;"))
        conn.commit()
    print("Success")
except Exception as e:
    print(f"Error: {e}")

from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text('ALTER TABLE ads ADD COLUMN last_republished_at TIMESTAMP NULL'))
    except Exception as e:
        print(e)
    try:
        conn.execute(text('ALTER TABLE ads ADD COLUMN republish_notification_sent BOOLEAN DEFAULT FALSE'))
    except Exception as e:
        print(e)
    conn.commit()
print("Migration done")

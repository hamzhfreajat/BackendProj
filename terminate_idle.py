import os
from sqlalchemy import text
from database import engine

print("Connecting to DB to terminate idle connections...")
with engine.connect() as conn:
    res = conn.execute(text("""
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE state = 'idle'
      AND pid <> pg_backend_pid();
    """))
    conn.commit()
    print(f'Terminated connections successfully.')

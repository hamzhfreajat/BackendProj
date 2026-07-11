import sys
import os
sys.path.append(os.getcwd())
from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Get count before
    res_before = conn.execute(text("SELECT COUNT(*) FROM telemetry_events WHERE event_name = 'error'")).fetchone()
    count_before = res_before[0]
    print(f'Errors before: {count_before}')

    # Delete
    conn.execute(text("DELETE FROM telemetry_events WHERE event_name = 'error'"))
    conn.commit()

    # Get count after
    res_after = conn.execute(text("SELECT COUNT(*) FROM telemetry_events WHERE event_name = 'error'")).fetchone()
    count_after = res_after[0]
    print(f'Errors after: {count_after}')

print('Cleared successfully.')

import sqlite3
import os

db_path = os.path.join(os.getcwd(), 'classifieds.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get count before
cursor.execute("SELECT COUNT(*) FROM telemetry_events WHERE event_name = 'error'")
count_before = cursor.fetchone()[0]
print(f'Errors before: {count_before}')

# Delete
cursor.execute("DELETE FROM telemetry_events WHERE event_name = 'error'")
conn.commit()

# Get count after
cursor.execute("SELECT COUNT(*) FROM telemetry_events WHERE event_name = 'error'")
count_after = cursor.fetchone()[0]
print(f'Errors after: {count_after}')

conn.close()
print('Cleared successfully.')

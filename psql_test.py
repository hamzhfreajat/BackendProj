import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
if not db_url:
    print("No DATABASE_URL found")
    import sys
    sys.exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT id, name_ar, city_id FROM regions WHERE name_ar LIKE '%المقابلة%';")
    rows = cur.fetchall()
    print("Found Regions:", rows)
except Exception as e:
    print("Failed to connect:", e)

import psycopg
import os
from dotenv import load_dotenv
load_dotenv()
conn = psycopg.connect(
    dbname=os.getenv("DB_NAME", "open"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)
conn.autocommit = True
cur = conn.cursor()

for col in ["is_featured", "is_hot"]:
    try:
        cur.execute(f"ALTER TABLE ads ADD COLUMN {col} BOOLEAN DEFAULT FALSE;")
        print(f"Added {col}")
    except Exception as e:
        print(f"{col} might already exist: {e}")

cur.close()
conn.close()

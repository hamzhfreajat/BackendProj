import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "open")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

conn_info = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")

try:
    with psycopg.connect(conn_info) as conn:
        with conn.cursor() as cur:
            print("Dropping constraints...")
            cur.execute("ALTER TABLE ads ALTER COLUMN title DROP NOT NULL;")
            cur.execute("ALTER TABLE ads ALTER COLUMN description DROP NOT NULL;")
            cur.execute("ALTER TABLE ads ALTER COLUMN price DROP NOT NULL;")
            cur.execute("ALTER TABLE ads ALTER COLUMN location DROP NOT NULL;")
            conn.commit()
            print("Successfully updated!")
except Exception as e:
    print(f"Error: {e}")

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "open")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def apply_migrations():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        print("Adding advanced profile columns to users table...")
        
        # bio
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;")
        
        # preferred_contact
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_contact VARCHAR(50);")
        
        # languages_spoken
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS languages_spoken JSONB;")
        
        # metrics
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deals_completed INTEGER DEFAULT 0;")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS cancellation_rate INTEGER DEFAULT 0;")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS buyer_satisfaction INTEGER DEFAULT 0;")
        
        # Fix defaults for existing rows exactly as previous schema migration
        cursor.execute("UPDATE users SET deals_completed = 0 WHERE deals_completed IS NULL;")
        cursor.execute("UPDATE users SET cancellation_rate = 0 WHERE cancellation_rate IS NULL;")
        cursor.execute("UPDATE users SET buyer_satisfaction = 100 WHERE buyer_satisfaction IS NULL;") # default to 100 on existing? Let's just say 0 for now as decided.

        print("Successfully applied advanced profile extensions schemas!")

    except Exception as e:
        print(f"Error applying migrations: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    apply_migrations()

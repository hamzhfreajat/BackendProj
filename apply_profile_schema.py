import os
from sqlalchemy import create_engine, text

# Use localhost to connect to the Windows machine's native postgres instance
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_NAME = os.getenv("DB_NAME", "open")
DB_HOST = os.getenv("DB_HOST", "localhost")

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

alter_statements = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_type VARCHAR(50) DEFAULT 'private';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS cover_image_url TEXT;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS overall_rating DECIMAL(3, 2) DEFAULT 0.0;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS response_rate INTEGER DEFAULT 100;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS average_response_time VARCHAR(50) DEFAULT 'Typically replies within 1 hour';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS trust_score INTEGER DEFAULT 50;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS followers_count INTEGER DEFAULT 0;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS following_count INTEGER DEFAULT 0;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_phone_verified BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_identity_verified BOOLEAN DEFAULT FALSE;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(100) DEFAULT '';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS shop_name VARCHAR(100);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS business_policy TEXT;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS shop_location TEXT;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS shop_hours VARCHAR(100);",
    
    """
    CREATE TABLE IF NOT EXISTS user_reviews (
        id SERIAL PRIMARY KEY,
        target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        reviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        rating DECIMAL(3, 2) NOT NULL,
        text TEXT NOT NULL,
        tags JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]

with engine.begin() as conn:
    for stmt in alter_statements:
        try:
            conn.execute(text(stmt))
            print(f"Success: {stmt[:50]}...")
        except Exception as e:
            print(f"Error executing {stmt[:50]}: {e}")

print("Schema update complete.")

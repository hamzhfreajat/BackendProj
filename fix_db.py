import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'classifieds')

pw = urllib.parse.quote_plus(DB_PASSWORD)
url = f"postgresql+psycopg://{DB_USER}:{pw}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(url)
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE saved_filters DROP COLUMN IF EXISTS match_count;"))
    conn.execute(text("ALTER TABLE saved_filters ADD COLUMN IF NOT EXISTS search_query VARCHAR(255);"))
    conn.commit()
print("Success!")

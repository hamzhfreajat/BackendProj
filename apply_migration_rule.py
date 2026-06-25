import os
import sys
from sqlalchemy import text
from database import engine

def create_table():
    try:
        with engine.begin() as conn:
            conn.execute(text('''
                CREATE TABLE IF NOT EXISTS facebook_autopost_rules (
                    id SERIAL PRIMARY KEY,
                    region_name TEXT UNIQUE NOT NULL,
                    threshold INTEGER DEFAULT 100,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            '''))
            print("Successfully created facebook_autopost_rules table.")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    create_table()

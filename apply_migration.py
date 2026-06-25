import os
import sys
from sqlalchemy import text
from database import engine

def add_column():
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE ads ADD COLUMN is_facebook_posted BOOLEAN DEFAULT FALSE;"))
            print("Successfully added is_facebook_posted to ads table.")
    except Exception as e:
        if 'already exists' in str(e):
            print("Column already exists.")
        else:
            print("Error:", e)

if __name__ == '__main__':
    add_column()

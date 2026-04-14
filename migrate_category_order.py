import os
import sys
from database import SessionLocal, engine, Base
from models import Category
from sqlalchemy import text

sys.stdout.reconfigure(encoding='utf-8')

def migrate_order_index():
    print("Adding temporary order_index columns to categories...")
    # SQL to add the column, using text over alembic for quick hotfix
    try:
        with engine.connect() as con:
            con.execute(text("ALTER TABLE categories ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0"))
            con.commit()
    except Exception as e:
        print(f"Warning/Error altering table (it may already exist): {e}")

    try:
        db = SessionLocal()
        categories = db.query(Category).order_by(Category.id.asc()).all()
        print(f"Found {len(categories)} categories to index.")
        
        index_track = 0
        for category in categories:
            category.order_index = index_track
            index_track += 1
            
        db.commit()
        print("Successfully applied initial order_index to all categories.")
    except Exception as e:
        print(f"Error migrating order_index: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_order_index()

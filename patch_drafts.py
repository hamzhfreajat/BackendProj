from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("Dropping NOT NULL constraints for drafts...")
        conn.execute(text("ALTER TABLE ads ALTER COLUMN title DROP NOT NULL;"))
        conn.execute(text("ALTER TABLE ads ALTER COLUMN description DROP NOT NULL;"))
        conn.execute(text("ALTER TABLE ads ALTER COLUMN price DROP NOT NULL;"))
        conn.execute(text("ALTER TABLE ads ALTER COLUMN location DROP NOT NULL;"))
        conn.commit()
        print("Successfully updated database schema!")
except Exception as e:
    print(f"Error updating schema: {e}")

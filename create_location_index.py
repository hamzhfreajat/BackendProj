from database import engine

from sqlalchemy import text

def create_index():
    with engine.connect() as con:
        con.execute(text("CREATE INDEX IF NOT EXISTS idx_ads_location_pattern ON ads (location text_pattern_ops);"))
        con.commit()
        print("Index created successfully!")

if __name__ == "__main__":
    create_index()

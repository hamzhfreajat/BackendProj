import asyncio
from database import SessionLocal
from sqlalchemy import text

def create_indexes():
    db = SessionLocal()
    try:
        # Create pg_trgm extension if not exists
        db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

        indexes_sql = [
            # GIN on TSVECTOR
            "CREATE INDEX IF NOT EXISTS idx_ad_search_vector ON ad_search_index USING GIN(search_vector);",
            
            # GIN on TEXT for Trigram Fuzzy Search
            "CREATE INDEX IF NOT EXISTS idx_ad_search_text_trgm ON ad_search_index USING GIN(search_text gin_trgm_ops);",
            
            # B-TREE on common filters for fast filtering
            "CREATE INDEX IF NOT EXISTS idx_ad_search_filters ON ad_search_index (category_id, city_id, region_id, deal_type, price);",
            
            # GIN on attributes JSONB
            "CREATE INDEX IF NOT EXISTS idx_ad_search_attributes ON ad_search_index USING GIN(attributes_jsonb);"
        ]

        for sql in indexes_sql:
            print(f"Executing: {sql}")
            db.execute(text(sql))
            
        db.commit()
        print("✅ Search Indexes created successfully.")
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_indexes()

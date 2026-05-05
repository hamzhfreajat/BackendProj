from sqlalchemy import text
from database import engine, Base
import models

def create_indexes():
    print("Creating tables if not exists...")
    models.Base.metadata.create_all(bind=engine)
    
    print("Setting up pg_trgm and indexes...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        
        # Create GIN index on search_vector
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_search_vector ON ad_search_index USING GIN(search_vector);"))
            print("Created idx_ad_search_vector")
        except Exception as e:
            print("Skipped idx_ad_search_vector:", e)
            
        # Create GIN index on search_text using trigrams
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_search_text_trgm ON ad_search_index USING GIN(search_text gin_trgm_ops);"))
            print("Created idx_ad_search_text_trgm")
        except Exception as e:
            print("Skipped idx_ad_search_text_trgm:", e)

        # Create structured indexes
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_search_structured ON ad_search_index(category_id, city_id, region_id, deal_type, price);"))
            print("Created idx_ad_search_structured")
        except Exception as e:
            print("Skipped idx_ad_search_structured:", e)

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ad_search_attributes ON ad_search_index USING GIN(attributes_jsonb);"))
            print("Created idx_ad_search_attributes")
        except Exception as e:
            print("Skipped idx_ad_search_attributes:", e)
            
    print("Done!")

if __name__ == "__main__":
    create_indexes()

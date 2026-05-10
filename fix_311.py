import os
import sys
import json
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath('.'))
from database import engine

with engine.begin() as conn:
    # 1. Delete all newly inserted items under 311 to clear duplicates and old icons
    conn.execute(text("DELETE FROM categories WHERE parent_id = 311 AND id > 1000"))
    
    # 2. Get all children of 10311 (تجاري للبيع)
    res = conn.execute(text("SELECT * FROM categories WHERE parent_id = 10311"))
    cats_10311 = [dict(row._mapping) for row in res]
    
    for cat in cats_10311:
        new_name = cat['name'].replace('للبيع', 'للايجار').replace('للبيع', 'للايجار')
        
        # fix slugs json
        if cat['slugs'] is not None:
            cat['slugs'] = json.dumps(cat['slugs'])
            
        # If it's the equivalent of 303 or 304, we UPDATE the existing 303 or 304 instead of inserting
        if cat['id'] == 10303:
            conn.execute(text("""
                UPDATE categories SET 
                    icon_name = :icon_name, 
                    color_hex = :color_hex, 
                    background_url = :background_url, 
                    tag = :tag, 
                    slugs = cast(:slugs as jsonb), 
                    order_index = :order_index, 
                    description = :description 
                WHERE id = 303
            """), cat)
        elif cat['id'] == 10304:
            conn.execute(text("""
                UPDATE categories SET 
                    icon_name = :icon_name, 
                    color_hex = :color_hex, 
                    background_url = :background_url, 
                    tag = :tag, 
                    slugs = cast(:slugs as jsonb), 
                    order_index = :order_index, 
                    description = :description 
                WHERE id = 304
            """), cat)
        else:
            # Generate new id
            max_id_res = conn.execute(text("SELECT MAX(id) FROM categories"))
            max_id = max_id_res.fetchone()[0] or 1000
            new_id = max_id + 1
            
            # Insert
            cat_insert = cat.copy()
            cat_insert['id'] = new_id
            cat_insert['name'] = new_name
            cat_insert['parent_id'] = 311
            
            conn.execute(text("""
                INSERT INTO categories (id, parent_id, name, description, icon_name, color_hex, background_url, tag, slugs, order_index) 
                VALUES (:id, :parent_id, :name, :description, :icon_name, :color_hex, :background_url, :tag, cast(:slugs as jsonb), :order_index)
            """), cat_insert)

    print("Done!")

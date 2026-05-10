import os
import sys
import json
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath('.'))
from database import engine

with engine.begin() as conn:
    res = conn.execute(text("SELECT id, name FROM categories WHERE parent_id = 311"))
    cats = [dict(row._mapping) for row in res]
    with open('categories_311.json', 'w', encoding='utf-8') as f:
        json.dump(cats, f, ensure_ascii=False, indent=2)

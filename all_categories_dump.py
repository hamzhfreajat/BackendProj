import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql = "SELECT id, name, parent_id FROM categories ORDER BY parent_id NULLS FIRST, id"
cats = db.execute(text(sql)).fetchall()

output = [{"id": c.id, "name": c.name, "parent_id": c.parent_id} for c in cats]

with open('all_categories_dump.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

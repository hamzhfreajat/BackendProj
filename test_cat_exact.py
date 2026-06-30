import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

ids = [301, 302, 3101, 3102, 3, 10301, 10302, 10101, 10102, 2]
sql = f"SELECT id, name FROM categories WHERE id IN {tuple(ids)}"
cats = db.execute(text(sql)).fetchall()

output = [{"id": c.id, "name": c.name} for c in cats]

with open('test_cat_exact.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

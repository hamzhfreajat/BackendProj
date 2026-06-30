import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql = "SELECT id, name FROM categories WHERE id IN (10101, 10301, 301, 302)"
cats = db.execute(text(sql)).fetchall()

output = []
for c in cats:
    output.append({"id": c.id, "name": c.name})

with open('test_cat_ids.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql = "SELECT id, name FROM categories WHERE name ILIKE '%شقق%' OR name ILIKE '%للبيع%' OR name ILIKE '%للايجار%' LIMIT 50"
cats = db.execute(text(sql)).fetchall()

output = []
for c in cats:
    output.append({"id": c.id, "name": c.name})

with open('test_categories.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

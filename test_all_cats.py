import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql = "SELECT id, name FROM categories"
cats = db.execute(text(sql)).fetchall()

output = [{"id": c.id, "name": c.name} for c in cats]

with open('test_all_cats.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

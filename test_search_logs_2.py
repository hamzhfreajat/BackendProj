import sys
import json
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

sql = "SELECT id, query_text, results_count, created_at FROM search_query_logs ORDER BY id DESC LIMIT 20"
rows = db.execute(text(sql)).fetchall()

output = []
for row in rows:
    output.append({
        "id": row.id,
        "query_text": row.query_text,
        "results_count": row.results_count,
        "created_at": str(row.created_at)
    })

with open('test_search_logs_2.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

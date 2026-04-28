import os
from database import SessionLocal
from models import Ad
from sqlalchemy import text

db = SessionLocal()
try:
    sql = text("EXPLAIN ANALYZE SELECT count(*) FROM ads WHERE location LIKE 'عمان%';")
    res = db.execute(sql).fetchall()
    for row in res:
        print(row[0])
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

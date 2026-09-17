from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
query = "SELECT id, title FROM ads WHERE ads::text LIKE '%0787224854%'"
result = db.execute(text(query)).fetchall()
print(f'Found {len(result)} ads')
for row in result:
    print(f'- ID: {row[0]}')

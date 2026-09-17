from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
query = "SELECT id FROM ads WHERE ads::text LIKE '%0772422663%'"
result = db.execute(text(query)).fetchall()
ids = [row[0] for row in result]
if ids:
    db.execute(text("DELETE FROM ads WHERE id = ANY(:ids)").bindparams(ids=ids))
    db.commit()
print(f'Deleted {len(ids)} ads with number 0772422663')

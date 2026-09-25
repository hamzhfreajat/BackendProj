import database, models
from sqlalchemy import text

db = next(database.get_db())
try:
    res = db.execute(text("SELECT 1")).scalar()
    print("Connection successful! Result:", res)
except Exception as e:
    print("Connection failed:", e)

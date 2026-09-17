from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
res = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='ads' AND column_name='market_price_status';")).fetchall()
print("Columns found:", res)

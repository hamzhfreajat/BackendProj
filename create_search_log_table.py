from database import engine
from models import SearchQueryLog
SearchQueryLog.__table__.create(bind=engine, checkfirst=True)
print("search_query_logs table created successfully.")

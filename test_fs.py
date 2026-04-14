import asyncio
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

import models
import scraper

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/classifieds_db"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

test_req = {
    "source_url": "https://www.facebook.com/groups/637038403908513/",
    "category_id": 301,
    "default_city": "عمان",
    "limit": 5
}

def run_test():
    db = SessionLocal()
    try:
        scraper.run_scraper_task(test_req, db)
        print("Status:", scraper.active_scrape_status)
    finally:
        db.close()

if __name__ == "__main__":
    run_test()

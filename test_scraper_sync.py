import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
import scraper, database

def main():
    db = database.SessionLocal()
    req = {
        "source_url": "https://web.facebook.com/groups/721423938231423/?locale=ar_AR&_rdc=1&_rdr#",
        "category_id": 301,
        "default_city": "عمان",
        "limit": 10
    }
    print(f"Starting synchronous test with limit: {req['limit']}...")
    scraper.run_scraper_task(req, db)
    print("Finished.")

if __name__ == "__main__":
    main()

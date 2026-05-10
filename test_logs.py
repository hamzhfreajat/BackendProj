import asyncio
from sqlalchemy.orm import Session
from database import SessionLocal
import models

def check_logs():
    db: Session = SessionLocal()
    try:
        logs = db.query(models.ScrapingLog).order_by(models.ScrapingLog.id.desc()).limit(5).all()
        for log in logs:
            print(f"ID: {log.id}, Group: {log.group_name}, Saved: {log.saved_ads}, Errors: {log.errors_count}, Time: {log.created_at}")
    finally:
        db.close()

if __name__ == "__main__":
    check_logs()

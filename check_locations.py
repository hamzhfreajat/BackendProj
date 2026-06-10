from database import SessionLocal
import models
from sqlalchemy import func

def main():
    db = SessionLocal()
    # Group by location and count
    results = db.query(models.Ad.location, func.count(models.Ad.id)).group_by(models.Ad.location).all()
    
    with open('locations_count.txt', 'w', encoding='utf-8') as f:
        for loc, count in results:
            f.write(f"{loc}: {count}\n")
        
if __name__ == '__main__':
    main()

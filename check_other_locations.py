from database import SessionLocal
import models

def main():
    db = SessionLocal()
    # Get last 20 ads with location 'عمان, أخرى'
    ads = db.query(models.Ad).filter(models.Ad.location == 'عمان, أخرى').order_by(models.Ad.id.desc()).limit(20).all()
    
    with open('other_locations_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"Found {len(ads)} ads in 'عمان, أخرى'\n")
        for ad in ads:
            f.write("-" * 50 + "\n")
            f.write(f"AD ID: {ad.id}\n")
            f.write(f"TITLE: {ad.title}\n")
            f.write(f"DESC: {ad.raw_description[:300]}..." if ad.raw_description else "NO DESC\n")
            f.write("\n")
        
if __name__ == '__main__':
    main()

import os
import sys
from sqlalchemy import text
from database import SessionLocal

sys.stdout.reconfigure(encoding='utf-8')

def run():
    db = SessionLocal()
    try:
        # Find ads where the location contains 'بدر' but not 'شفا'
        sql_select = text("""
            SELECT id, title, location, raw_description, description 
            FROM ads 
            WHERE location LIKE '%بدر%' AND location NOT LIKE '%شفا%'
        """)
        
        ads = db.execute(sql_select).fetchall()
        print(f"Total ads with 'بدر' in location (and no 'شفا'): {len(ads)}")
        
        updated_count = 0
        for ad in ads:
            ad_id = ad[0]
            title = ad[1] or ''
            location = ad[2] or ''
            raw = ad[3] or ''
            desc = ad[4] or ''
            
            combined_text = title + " " + raw + " " + desc
            
            # Check if "شفا" or "شفابدران" or "شفا بدران" is in the text
            if "شفا" in combined_text:
                print(f"Match found! Ad {ad_id}: Location is '{location}'. Text contains 'شفا بدران'")
                
                sql_update = text("UPDATE ads SET location = 'عمان, شفا بدران' WHERE id = :id")
                db.execute(sql_update, {"id": ad_id})
                updated_count += 1
                
        db.commit()
        print(f"\nSuccessfully updated {updated_count} ads to 'عمان, شفا بدران'!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run()

import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

from database import SessionLocal
from models import Category

VALID_ROOTS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

def cleanup():
    db = SessionLocal()
    try:
        orphans = db.query(Category).filter(
            Category.parent_id == None,
            Category.id.notin_(VALID_ROOTS)
        ).all()
        
        count = len(orphans)
        for c in orphans:
            print(f"Deleting Orphan: {c.id} - {c.name}")
            db.delete(c)
        
        db.commit()
        print(f"Deleted {count} orphaned root categories and all their descendants.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()

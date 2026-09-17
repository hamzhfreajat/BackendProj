import traceback
from database import SessionLocal
from models import Ad

db = SessionLocal()
try:
    ad = db.query(Ad).filter(Ad.id == 28087).first()
    if not ad:
        print("Ad not found!")
    else:
        db.delete(ad)
        db.commit()
        print("Success")
except Exception as e:
    print("ERROR:")
    traceback.print_exc()
finally:
    db.rollback()
    db.close()

from database import SessionLocal
import models
from sqlalchemy import and_

db = SessionLocal()

# We need to delete all categories starting with 5040 or 5041 up to 50499
# meaning id > 50400 and id < 50500
targets = db.query(models.Category).filter(
    and_(
        models.Category.id > 50400,
        models.Category.id < 50500
    )
).all()

count = len(targets)
for t in targets:
    db.delete(t)

db.commit()
print(f"Deleted {count} orphaned categories from 504xx")

from database import SessionLocal
import models
from sqlalchemy import and_

db = SessionLocal()

# We need to delete ALL categories that start with "504" except "504" itself.
# This catches 50401, 5040101, 50499, etc.
targets = db.query(models.Category).filter(
    and_(
        models.Category.id.cast(__import__("sqlalchemy").String).like("504%"),
        models.Category.id != 504
    )
).all()

count = len(targets)
for t in targets:
    db.delete(t)

db.commit()
print(f"Deleted {count} escaped orphaned categories starting with 504")

# Let us also output how many top level categories remain just to be absolutely certain!
mains = db.query(models.Category).filter(models.Category.parent_id == None).count()
print(f"Total Main Categories in DB: {mains}")

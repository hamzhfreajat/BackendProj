from database import SessionLocal
import models
from sqlalchemy import and_

db = SessionLocal()

# We need to delete ALL categories that start with "7" except "7" itself.
# This prepares the space so there are no rogue orphaned duplicates
targets = db.query(models.Category).filter(
    and_(
        models.Category.id.cast(__import__("sqlalchemy").String).like("7%"),
        models.Category.id != 7
    )
).all()

count = len(targets)
for t in targets:
    db.delete(t)

db.commit()
print(f"Deleted {count} old categories starting with 7")

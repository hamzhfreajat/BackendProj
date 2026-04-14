from database import SessionLocal
import models
from sqlalchemy import or_

db = SessionLocal()

# We need to delete all categories starting with 901
# ID 901 itself, and anything LIKE '901%'
targets = db.query(models.Category).filter(
    or_(
        models.Category.id == 901,
        models.Category.id.cast(__import__("sqlalchemy").String).like("901%")
    )
).all()

count = len(targets)
for t in targets:
    db.delete(t)

db.commit()
print(f"Deleted {count} categories under 901")

import os, sys, codecs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from database import SessionLocal
from models import Category
from sqlalchemy import text

db = SessionLocal()
db.execute(text("UPDATE categories SET icon_name = REPLACE(icon_name, '/static/icons/', '/uploads/icons/') WHERE icon_name LIKE '/static/icons/%'"))
db.commit()
print("Updated icon paths from /static/icons/ to /uploads/icons/")
db.close()

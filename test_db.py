import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

encoded_password = urllib.parse.quote_plus('p2j9ggm6cWLAhhVTsbNzYFqK')
URL = f'postgresql+psycopg://postgres:{encoded_password}@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q'
engine = create_engine(URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

result = db.execute(text('SELECT id, name FROM categories WHERE id IN (3023, 10015)')).fetchall()
print('Categories:', result)

result_groups = db.execute(text('SELECT id, name, category_id FROM saved_groups WHERE category_id IN (3023, 10015)')).fetchall()
print('SavedGroups:', result_groups)

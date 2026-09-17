from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
for table in tables:
    for fk in inspector.get_foreign_keys(table):
        if 'ads' in fk['referred_table']:
            print(f"{table} -> ads.id : {fk.get('options')}")

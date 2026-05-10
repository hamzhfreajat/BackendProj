import os
import sys
from sqlalchemy import create_engine, text

sys.path.append(os.path.abspath('.'))
from database import engine

with engine.begin() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='categories'"))
    cols = [row[0] for row in res]
    print(cols)

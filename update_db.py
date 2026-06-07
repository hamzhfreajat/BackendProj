import io, sys
from sqlalchemy import create_engine, text
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
engine = create_engine('postgresql+psycopg2://postgres:123456@localhost:5432/open')
with engine.connect() as conn:
    conn.execute(text("UPDATE categories SET parent_id = 2 WHERE id = 10313"))
    conn.commit()
    res = conn.execute(text("SELECT id, parent_id, name FROM categories WHERE id = 10313"))
    for row in res:
        print(row)

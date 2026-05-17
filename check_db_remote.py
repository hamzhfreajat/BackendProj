import os
from sqlalchemy import text
from database import engine

# run query
with engine.connect() as conn:
    res = conn.execute(text("SELECT id, name, parent_id FROM categories WHERE name LIKE '%فندقي%' OR name LIKE '%مخدوم%'"))
    with open('db_output_remote.txt', 'w', encoding='utf-8') as f:
        f.write("Categories:\n")
        for row in res:
            f.write(str(row) + "\n")

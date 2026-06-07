import io, sys
from sqlalchemy import create_engine, text
import urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ensure the password is url-encoded properly if it has special characters
password = urllib.parse.quote_plus('p2j9ggm6cWLAhhVTsbNzYFqK')
db_url = f"postgresql+psycopg2://cmnynjgg70001aumle0zkfovm:{password}@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q"
engine = create_engine(db_url)

with engine.connect() as conn:
    with conn.begin():
        print("Checking category 10313 before update:")
        res = conn.execute(text("SELECT id, parent_id, name, icon_name FROM categories WHERE id = 10313")).fetchone()
        print(res)
        
        print("Updating parent_id for 10313 to 2...")
        conn.execute(text("UPDATE categories SET parent_id = 2 WHERE id = 10313"))
        
        print("Checking category 10313 after update:")
        res2 = conn.execute(text("SELECT id, parent_id, name, icon_name FROM categories WHERE id = 10313")).fetchone()
        print(res2)

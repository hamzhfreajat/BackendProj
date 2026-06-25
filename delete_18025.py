import urllib.parse
from sqlalchemy import create_engine, text

encoded_password = urllib.parse.quote_plus('p2j9ggm6cWLAhhVTsbNzYFqK')
engine = create_engine(f'postgresql://postgres:{encoded_password}@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q')

with engine.connect() as conn:
    print("Deleting 18025...")
    conn.execute(text("DELETE FROM categories WHERE id = 18025"))
    conn.commit()
    print("Deleted 18025!")

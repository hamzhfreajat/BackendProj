import urllib.parse
from sqlalchemy import create_engine, text

encoded_password = urllib.parse.quote_plus('p2j9ggm6cWLAhhVTsbNzYFqK')
engine = create_engine(f'postgresql://postgres:{encoded_password}@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q')

with engine.connect() as conn:
    # Check how many rows will be affected
    res = conn.execute(text("""
    SELECT count(*) FROM scraping_logs WHERE group_name ~ '^\\([0-9]+\\+?\\)\\s*';
    """)).scalar()
    print(f"Rows to clean: {res}")
    
    # Update the rows
    conn.execute(text("""
    UPDATE scraping_logs 
    SET group_name = regexp_replace(group_name, '^\\([0-9]+\\+?\\)\\s*', '')
    WHERE group_name ~ '^\\([0-9]+\\+?\\)\\s*';
    """))
    conn.commit()
    print("Database updated successfully!")

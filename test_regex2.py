import urllib.parse
from sqlalchemy import create_engine, text

encoded_password = urllib.parse.quote_plus('p2j9ggm6cWLAhhVTsbNzYFqK')
engine = create_engine(f'postgresql://postgres:{encoded_password}@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q')

with engine.connect() as conn:
    res = conn.execute(text("""
    SELECT group_name 
    FROM scraping_logs 
    WHERE group_name LIKE '%سوق معان%' 
    ORDER BY created_at DESC
    LIMIT 10
    """)).fetchall()
    
    for r in res:
        print(r[0])

import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    cur.execute("""
        SELECT a.location 
        FROM ads a
        JOIN ad_search_index idx ON a.id = idx.ad_id
        WHERE idx.search_text ILIKE '%الجبيهه%'
        LIMIT 10
    """)
    rows = cur.fetchall()
    
    with open('ad_locs.txt', 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(str(r[0]) + '\n')
except Exception as e:
    print('ERROR:', e)

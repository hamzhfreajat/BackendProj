import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT id, title, location, attributes FROM ads WHERE id = 25989")
    res = cur.fetchall()
    
    with open('out_h6.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"Ad {r[0]}: Title: {r[1]}, Location: {r[2]}, Attr: {r[3]}\n")
            
    # Test ILIKE query directly
    cur.execute("SELECT id FROM ads WHERE id = 25989 AND REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(location, 'أ', 'ا'), 'إ', 'ا'), 'آ', 'ا'), 'ة', 'ه'), 'ى', 'ي'), 'ي', 'ي') ILIKE 'اربد, حكما%'")
    res2 = cur.fetchall()
    with open('out_h6.txt', 'a', encoding='utf-8') as f:
        f.write(f"ILIKE Match: {len(res2) > 0}\n")
    
except Exception as e:
    print('ERROR:', e)

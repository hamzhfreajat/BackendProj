import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT id, title, location, attributes FROM ads WHERE title LIKE '%فاخرة للبيع في حكما%'")
    res = cur.fetchall()
    
    with open('out_h3.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"Ad {r[0]}: Title: {r[1]}, Location: {r[2]}, Attr: {r[3]}\n")
    
except Exception as e:
    print('ERROR:', e)

import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT category_id, is_published, is_paused, is_sold, is_rejected FROM ads WHERE id = 25989")
    res = cur.fetchone()
    
    with open('out_h8.txt', 'w', encoding='utf-8') as f:
        f.write(f"Ad 25989 info: {res}\n")
        
except Exception as e:
    print('ERROR:', e)

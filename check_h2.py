import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT name_ar, city_id FROM regions WHERE name_ar = 'حكما'")
    res = cur.fetchall()
    
    with open('out_h2.txt', 'w', encoding='utf-8') as f:
        f.write(f"Regions with name حكما: {res}\n")
    
except Exception as e:
    print('ERROR:', e)

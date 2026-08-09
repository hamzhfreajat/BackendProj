import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    with open('loc_spelling.txt', 'w', encoding='utf-8') as f:
        cur.execute("SELECT COUNT(id) FROM ads WHERE location = 'عمان, جبيهة'")
        f.write(f"عمان, جبيهة: {cur.fetchone()[0]}\n")
        
        cur.execute("SELECT COUNT(id) FROM ads WHERE location = 'عمان, الجبيهة'")
        f.write(f"عمان, الجبيهة: {cur.fetchone()[0]}\n")
        
        cur.execute("SELECT COUNT(id) FROM ads WHERE location ILIKE 'عمان, %جبيه%'")
        f.write(f"عمان, *جبيه*: {cur.fetchone()[0]}\n")
except Exception as e:
    print('ERROR:', e)

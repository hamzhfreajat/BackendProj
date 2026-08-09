import psycopg2

try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT id, location FROM ads WHERE title LIKE '%حكما%'")
    ads = cur.fetchall()
    with open('out_h.txt', 'w', encoding='utf-8') as f:
        f.write(f"Ads: {ads}\n")
        for ad in ads:
            cur.execute("SELECT search_text FROM ad_search_index WHERE ad_id = %s", (ad[0],))
            res = cur.fetchone()
            f.write(f"Ad {ad[0]} location in DB: {ad[1]}\n")
            f.write(f"Ad {ad[0]} index: {res[0][:100] if res else 'NO INDEX'}\n")
        
except Exception as e:
    print('ERROR:', e)

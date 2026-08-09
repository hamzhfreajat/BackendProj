import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT search_text FROM ad_search_index WHERE ad_id = 25989")
    res = cur.fetchone()
    
    with open('out_h7.txt', 'w', encoding='utf-8') as f:
        f.write(f"Ad 25989 search_text: {res[0] if res else 'NO INDEX'}\n")
        
except Exception as e:
    print('ERROR:', e)

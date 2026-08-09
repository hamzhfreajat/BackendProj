import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(DISTINCT ip_address) FROM rate_limit_logs")
    print('Distinct IPs in rate limits:', cur.fetchone()[0])
    
    cur.execute("SELECT COUNT(DISTINCT ip_address) FROM ads")
    print('Distinct IPs that posted ads:', cur.fetchone()[0])
    
except Exception as e:
    print('ERROR:', e)

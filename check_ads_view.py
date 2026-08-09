import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%دوار الداخليه%'")
    print('دوار الداخلية Ads:', cur.fetchone()[0])
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%الجبيهه%'")
    print('جبيهة Ads:', cur.fetchone()[0])
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%المدينه الرياضيه%'")
    print('المدينة الرياضية Ads:', cur.fetchone()[0])
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%دوار الواحه%'")
    print('دوار الواحة Ads:', cur.fetchone()[0])
except Exception as e:
    print('ERROR:', e)

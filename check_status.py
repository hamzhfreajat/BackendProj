import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    results = []
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%دوار الداخليه%'")
    results.append(f'دوار الداخلية Ads: {cur.fetchone()[0]}')
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%الجبيهه%'")
    results.append(f'الجبيهة Ads: {cur.fetchone()[0]}')
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%المدينه الرياضيه%'")
    results.append(f'المدينة الرياضية Ads: {cur.fetchone()[0]}')
    
    cur.execute("SELECT COUNT(ad_id) FROM ad_search_index WHERE search_text ILIKE '%دوار الواحه%'")
    results.append(f'دوار الواحة Ads: {cur.fetchone()[0]}')
    
    with open('ads_counts.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(results))
        
except Exception as e:
    with open('ads_counts.txt', 'w', encoding='utf-8') as f:
        f.write(f'ERROR: {e}')

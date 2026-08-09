import psycopg2
import sys

db_host = '178.104.204.148'
db_port = '9000'
db_name = 'cmnynjgg90003aumlerff4j9q'
db_user = 'postgres'
db_pass = 'p2j9ggm6cWLAhhVTsbNzYFqK'

try:
    conn = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_pass)
    cur = conn.cursor()
    
    regions = [
        'دوار الداخلية', 'جبيهة', 'الجبيهة', 'المدينة الرياضية', 
        'دوار الواحة', 'ابو نصير', 'ام زويتيه', 'ام زويتينة',
        'ضاحية الرشيد', 'ام السماق', 'شارع المدينة المنورة', 'شارع المدينة'
    ]
    
    for r in regions:
        cur.execute('''
            SELECT r.id, r.name_ar, r.name_en 
            FROM regions r
            LEFT JOIN region_aliases ra ON ra.region_id = r.id
            WHERE r.name_ar = %s OR ra.alias_name = %s
            LIMIT 1
        ''', (r, r))
        res = cur.fetchone()
        if res:
            print(f'FOUND: {r} -> ID: {res[0]}, Name: {res[1]}')
        else:
            print(f'MISSING: {r}')
            
except Exception as e:
    print(e)

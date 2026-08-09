import json
import psycopg2
import re

db_host = '178.104.204.148'
db_port = '9000'
db_name = 'cmnynjgg90003aumlerff4j9q'
db_user = 'postgres'
db_pass = 'p2j9ggm6cWLAhhVTsbNzYFqK'

def normalize_arabic(text):
    if not text: return ""
    text = re.sub(r'[أإآ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[ًٌٍَُِّْ]', '', text)
    text = re.sub(r'[()\[\]\{\}\.,!?"\'-]', ' ', text)
    return text.lower().strip()

try:
    conn = psycopg2.connect(host=db_host, port=db_port, dbname=db_name, user=db_user, password=db_pass)
    conn.autocommit = False
    cur = conn.cursor()
    
    # Get city_id for Amman
    cur.execute("SELECT id FROM cities WHERE name_ar = 'عمان' LIMIT 1")
    amman_city_id = cur.fetchone()[0]
    
    with open('target_regions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    missing_added = []
    
    for item in data['values']:
        label = item['label'].strip()
        if label == "أخرى" or label == "اخري":
            continue
            
        search_field = item.get('search_field', '')
        
        # Check if region exists by exact name_ar OR alias
        cur.execute("""
            SELECT r.id 
            FROM regions r
            LEFT JOIN region_aliases ra ON ra.region_id = r.id
            WHERE r.name_ar = %s OR ra.alias_name = %s
            LIMIT 1
        """, (label, label))
        
        res = cur.fetchone()
        
        if not res:
            # Check normalized name just in case
            norm_label = normalize_arabic(label)
            cur.execute("SELECT id FROM regions WHERE name_ar = %s", (norm_label,))
            res2 = cur.fetchone()
            if not res2:
                # Extract English name from search_field if possible
                parts = search_field.split()
                # Find the first english character
                en_parts = [p for p in parts if re.search(r'[a-zA-Z]', p)]
                name_en = ' '.join(en_parts) if en_parts else label
                
                # INSERT
                cur.execute(
                    "INSERT INTO regions (city_id, name_ar, name_en) VALUES (%s, %s, %s) RETURNING id",
                    (amman_city_id, label, name_en)
                )
                new_id = cur.fetchone()[0]
                
                # Insert the normalized version as alias if different
                if norm_label != label:
                    cur.execute(
                        "INSERT INTO region_aliases (region_id, alias_name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                        (new_id, norm_label)
                    )
                
                missing_added.append(label)
                
    conn.commit()
    
    # Now explicitly check the user's specific missing list just in case they are not in the JSON but requested anyway!
    specific_missing = [
        'دوار الداخلية', 'دوار الواحة', 'شارع المدينة المنورة'
    ]
    for sp in specific_missing:
        cur.execute("""
            SELECT r.id 
            FROM regions r
            LEFT JOIN region_aliases ra ON ra.region_id = r.id
            WHERE r.name_ar = %s OR ra.alias_name = %s
            LIMIT 1
        """, (sp, sp))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO regions (city_id, name_ar, name_en) VALUES (%s, %s, %s) RETURNING id",
                (amman_city_id, sp, sp)
            )
            new_id = cur.fetchone()[0]
            norm_sp = normalize_arabic(sp)
            if norm_sp != sp:
                cur.execute(
                    "INSERT INTO region_aliases (region_id, alias_name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (new_id, norm_sp)
                )
            missing_added.append(sp)
    
    conn.commit()
    print("Added the following missing regions:", missing_added)
    
except Exception as e:
    if 'conn' in locals(): conn.rollback()
    print("ERROR:", e)

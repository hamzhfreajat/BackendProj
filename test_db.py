import psycopg2, json
conn = psycopg2.connect(host='178.104.204.148', port=9000, dbname='cmnynjgg90003aumlerff4j9q', user='cmnynjgg70001aumle0zkfovm', password='z9l0aau7lAGSmmCGghGwKNbP')
cur = conn.cursor()
cur.execute("SELECT id, name, parent_id FROM categories WHERE name LIKE '%سكني%'")
res = []
for row in cur.fetchall():
    cur.execute("SELECT id, name FROM categories WHERE parent_id = %s", (row[0],))
    res.append({'id': row[0], 'name': row[1], 'children': cur.fetchall()})
with open('out.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=2)

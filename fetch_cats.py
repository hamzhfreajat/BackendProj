import psycopg

conn = psycopg.connect('postgresql://postgres:123456@localhost:5432/open')
cur = conn.cursor()

cur.execute('SELECT id, name, parent_id FROM categories WHERE id=18023 OR id=10315 OR id=18025 OR parent_id=18023')
res = cur.fetchall()

with open('output2.txt', 'w', encoding='utf-8') as f:
    for row in res:
        f.write(str(row) + '\n')

import psycopg

conn = psycopg.connect('postgresql://postgres:123456@localhost:5432/open')
cur = conn.cursor()

# Check for both "شقق فندقية" and "ستوديو فندقي"
cur.execute("SELECT id, name, parent_id FROM categories WHERE name LIKE '%فندقي%';")
categories = cur.fetchall()

with open('db_output.txt', 'w', encoding='utf-8') as f:
    f.write("Categories:\n")
    for c in categories:
        f.write(str(c) + "\n")

    cur.execute("SELECT id, name, parent_id FROM categories WHERE name LIKE '%مخدوم%';")
    categories_2 = cur.fetchall()

    f.write("Categories with makhdoom:\n")
    for c in categories_2:
        f.write(str(c) + "\n")

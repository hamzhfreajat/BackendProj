import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import psycopg2

conn = psycopg2.connect("host=localhost port=5432 dbname=open user=postgres password=123456")
cur = conn.cursor()

# Check direct children of "سيارات للبيع" (id=101)
cur.execute("SELECT id, name, parent_id FROM categories WHERE parent_id = 101 ORDER BY name")
children = cur.fetchall()
print(f"=== Direct children of 'سيارات للبيع' (id=101) - total: {len(children)} ===")
for c in children:
    print(f"  id={c[0]}, name={c[1]}")

# Also check "سيارات للإيجار" (id=102) 
cur.execute("SELECT id, name, parent_id FROM categories WHERE parent_id = 102 ORDER BY name")
rent_children = cur.fetchall()
print(f"\n=== Direct children of 'سيارات للإيجار' (id=102) - total: {len(rent_children)} ===")
for c in rent_children:
    print(f"  id={c[0]}, name={c[1]}")

# Check the top-level "سيارات ومركبات" (id=1)
cur.execute("SELECT id, name, parent_id FROM categories WHERE parent_id = 1 ORDER BY name")
top_children = cur.fetchall()
print(f"\n=== Direct children of 'سيارات ومركبات' (id=1) - total: {len(top_children)} ===")
for c in top_children:
    print(f"  id={c[0]}, name={c[1]}")

conn.close()

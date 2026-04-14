import psycopg, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# Find all Hyundai brands under 101
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND (name LIKE '%هيونداي%' OR name LIKE '%هونداي%' OR name LIKE '%Hyundai%')")
brands = cur.fetchall()
print(f"Hyundai brands under 101: {brands}")

for bid, bname in brands:
    cur.execute("SELECT id, name FROM categories WHERE parent_id = %s ORDER BY name", (bid,))
    models = cur.fetchall()
    print(f"\n  [{bid}] {bname} -> {len(models)} models:")
    for mid, mname in models:
        print(f"    [{mid}] {mname}")

# Also check 101124 directly
print("\n--- Checking 101124 directly ---")
cur.execute("SELECT id, name, parent_id FROM categories WHERE id = 101124")
row = cur.fetchone()
if row:
    print(f"[{row[0]}] {row[1]} parent={row[2]}")
    cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 101124")
    print(f"  Children count: {cur.fetchone()[0]}")
else:
    print("101124 does NOT exist!")

conn.close()

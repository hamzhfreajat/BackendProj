"""Fix remaining Chinese car models under 1017 - split to correct brands."""
import psycopg
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# Find the new Chinese brand IDs by English slug
brands = {}
for slug in ['mg', 'byd', 'changan', 'geely']:
    cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND slugs::text LIKE %s", (f'%"{slug}"%',))
    row = cur.fetchone()
    if row:
        brands[slug] = (row[0], row[1])
        print(f"  Found: {slug} -> [{row[0]}] {row[1]}")
    else:
        print(f"  NOT FOUND: {slug}")

# Get all remaining models under 1017
cur.execute("SELECT id, name FROM categories WHERE parent_id = 1017 ORDER BY name")
models = cur.fetchall()
print(f"\nRemaining models under 1017: {len(models)}")

# MG models: names starting with "MG " or specific MG models
mg_names = set()
byd_names = {'Atto 3', 'Destroyer 05', 'Dolphin', 'E2', 'E3', 'E6', 'F0', 'F3', 'F3R', 'F5', 'F6', 'F7',
             'G3', 'Han', 'Leopard 5', 'Leopard 7', 'Leopard 8', 'Qin', 'S6', 'Seagull', 'Seal', 'Shark 6',
             'Song L', 'Song Max', 'Song Plus', 'Song Pro', 'Tang', 'Yuan'}
geely_names = {'Azkarra', 'CK', 'Coolray', 'EC7', 'EC8', 'Emgrand', 'GC2', 'GC5', 'GC6', 'GC7',
               'Geometry C', 'Geometry E', 'GX2', 'GX3 Pro', 'Imperial', 'LC', 'Maple Leaf 60s', 'MK',
               'Monjaro', 'Okavango', 'Radar', 'S5', 'SC7', 'Starray', 'Tugella'}
changan_names = {'Alsvin', 'Benni', 'Chana', 'Cosmos', 'CS15', 'CS35', 'CS75', 'CS85', 'CS95',
                 'CX20', 'CX30', 'CX70', 'Deepal', 'E-Star', 'Eado', 'Eado DT', 'Eado EV', 'Eado XT',
                 'Hunter', 'Lumin', 'Sania', 'SL03', 'UNI-K', 'UNI-S', 'UNI-T', 'UNI-V', 'V3', 'V7', 'X7'}
# MG specific non-prefixed models
mg_specific = {'Cyberster', 'Pilot', 'Rakan', 'T60', 'Whale'}

moved = {'mg': 0, 'byd': 0, 'geely': 0, 'changan': 0, 'deleted': 0, 'unknown': []}

for mid, mname in models:
    if mname == 'Other':
        cur.execute("DELETE FROM categories WHERE id = %s", (mid,))
        moved['deleted'] += 1
    elif mname.startswith('MG ') or mname in mg_specific:
        if 'mg' in brands:
            # Check if this model already exists under the new MG brand
            cur.execute("SELECT id FROM categories WHERE parent_id = %s AND name = %s", (brands['mg'][0], mname))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM categories WHERE id = %s", (mid,))
                moved['deleted'] += 1
            else:
                cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (brands['mg'][0], mid))
                moved['mg'] += 1
    elif mname in byd_names:
        if 'byd' in brands:
            cur.execute("SELECT id FROM categories WHERE parent_id = %s AND name = %s", (brands['byd'][0], mname))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM categories WHERE id = %s", (mid,))
                moved['deleted'] += 1
            else:
                cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (brands['byd'][0], mid))
                moved['byd'] += 1
    elif mname in geely_names:
        if 'geely' in brands:
            cur.execute("SELECT id FROM categories WHERE parent_id = %s AND name = %s", (brands['geely'][0], mname))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM categories WHERE id = %s", (mid,))
                moved['deleted'] += 1
            else:
                cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (brands['geely'][0], mid))
                moved['geely'] += 1
    elif mname in changan_names:
        if 'changan' in brands:
            cur.execute("SELECT id FROM categories WHERE parent_id = %s AND name = %s", (brands['changan'][0], mname))
            existing = cur.fetchone()
            if existing:
                cur.execute("DELETE FROM categories WHERE id = %s", (mid,))
                moved['deleted'] += 1
            else:
                cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (brands['changan'][0], mid))
                moved['changan'] += 1
    else:
        moved['unknown'].append((mid, mname))

print(f"\nResults:")
print(f"  MG: {moved['mg']} moved")
print(f"  BYD: {moved['byd']} moved")
print(f"  Geely: {moved['geely']} moved")
print(f"  Changan: {moved['changan']} moved")
print(f"  Deleted (duplicates/Other): {moved['deleted']}")
print(f"  Unknown: {len(moved['unknown'])}")
for mid, mname in moved['unknown']:
    print(f"    [{mid}] {mname}")

# Check remaining under 1017
cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 1017")
remaining = cur.fetchone()[0]
print(f"\nRemaining under 1017: {remaining}")

if remaining == 0:
    cur.execute("DELETE FROM categories WHERE id = 1017")
    print("Deleted old Chinese cars brand (1017)")
else:
    # Delete remaining items
    cur.execute("SELECT id, name FROM categories WHERE parent_id = 1017")
    for row in cur.fetchall():
        print(f"  Deleting remaining [{row[0]}] {row[1]}")
        cur.execute("DELETE FROM categories WHERE id = %s", (row[0],))
    cur.execute("DELETE FROM categories WHERE id = 1017")
    print("Deleted old Chinese cars brand (1017) and remaining children")

# Final verification
cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 101")
print(f"\nFinal brands under 'cars for sale' (101): {cur.fetchone()[0]}")
cur.execute("SELECT id, name FROM categories WHERE id BETWEEN 1011 AND 1017")
old = cur.fetchall()
if old:
    print(f"WARNING: Old brands still exist: {old}")
else:
    print("All old brands (1011-1017) successfully removed!")

conn.commit()
print("\n=== COMMITTED ===")
conn.close()

"""Final verification of car brand structure."""
import psycopg
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# All brands under 101
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 ORDER BY name")
brands = cur.fetchall()
print(f"Total brands under 'سيارات للبيع' (101): {len(brands)}")
print()

# Check each brand has models
brands_with_models = 0
brands_without_models = 0
for bid, bname in brands:
    cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = %s", (bid,))
    count = cur.fetchone()[0]
    if count > 0:
        brands_with_models += 1
    else:
        brands_without_models += 1

print(f"Brands WITH models: {brands_with_models}")
print(f"Brands WITHOUT models: {brands_without_models}")

# Check no old brands remain
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id < 10000")
old = cur.fetchall()
if old:
    print(f"\nWARNING: Old-style brands still exist:")
    for r in old:
        print(f"  [{r[0]}] {r[1]}")
else:
    print("\nNo old-style brands remain (all IDs >= 101000) ✓")

# Check Honda
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101122 ORDER BY name LIMIT 5")
honda = cur.fetchall()
print(f"\nHonda (101122) sample models: {[r[1] for r in honda]}")

# Check the new Toyota
cur.execute("SELECT id, name FROM categories WHERE name = 'تويوتا' AND parent_id = 101")
toyota = cur.fetchone()
if toyota:
    cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = %s", (toyota[0],))
    count = cur.fetchone()[0]
    print(f"Toyota [{toyota[0]}] has {count} models")
    cur.execute("SELECT id, name FROM categories WHERE parent_id = %s ORDER BY name LIMIT 5", (toyota[0],))
    sample = cur.fetchall()
    print(f"  Sample: {[r[1] for r in sample]}")

# Check Hyundai
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101124 ORDER BY name LIMIT 5")
hyundai = cur.fetchall()
print(f"\nHyundai (101124) sample models: {[r[1] for r in hyundai]}")

# Orphan ads check
cur.execute("SELECT COUNT(*) FROM ads WHERE category_id NOT IN (SELECT id FROM categories)")
print(f"\nOrphan ads: {cur.fetchone()[0]}")

print("\n=== VERIFICATION COMPLETE ===")
conn.close()

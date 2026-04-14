import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import psycopg2

conn = psycopg2.connect("host=localhost port=5432 dbname=open user=postgres password=123456")
cur = conn.cursor()

# Get ALL brands under both sale (101) and rental (102)
cur.execute("SELECT id, name FROM categories WHERE parent_id IN (101, 102) ORDER BY id")
brands = cur.fetchall()

all_bad = []
bad_details = []

for brand_id, brand_name in brands:
    cur.execute("SELECT id, name FROM categories WHERE parent_id = %s ORDER BY id", (brand_id,))
    children = cur.fetchall()
    if not children:
        continue
    
    bad_kids = []
    for child_id, child_name in children:
        if brand_id >= 101000:
            # New brands (101000+ and 102000+) should have NO children at all
            bad_kids.append((child_id, child_name))
        elif brand_id >= 1011 and brand_id <= 1017:
            # Old brands - only children with id >= 200000 are valid car models
            if child_id < 200000:
                bad_kids.append((child_id, child_name))
    
    if bad_kids:
        bad_details.append((brand_id, brand_name, bad_kids))
        for cid, cname in bad_kids:
            all_bad.append(cid)

# Summary only
print(f"Brands with wrong children: {len(bad_details)}")
print(f"Total misplaced categories (direct): {len(all_bad)}")

# Now collect all descendants of bad categories too
def get_all_descendants(cur, cat_id):
    ids = [cat_id]
    cur.execute("SELECT id FROM categories WHERE parent_id = %s", (cat_id,))
    for row in cur.fetchall():
        ids.extend(get_all_descendants(cur, row[0]))
    return ids

all_to_delete = []
for bid in all_bad:
    descendants = get_all_descendants(cur, bid)
    all_to_delete.extend(descendants)

all_to_delete = list(set(all_to_delete))
print(f"Total including all descendants: {len(all_to_delete)}")

# Check which have ads
ads_cats = []
for bid in all_to_delete:
    cur.execute("SELECT COUNT(*) FROM ads WHERE category_id = %s", (bid,))
    count = cur.fetchone()[0]
    if count > 0:
        cur.execute("SELECT name, parent_id FROM categories WHERE id = %s", (bid,))
        row = cur.fetchone()
        ads_cats.append((bid, row[0] if row else "?", count))

print(f"\nCategories with ads: {len(ads_cats)}")
for ac in ads_cats:
    print(f"  id={ac[0]}, name={ac[1]}, ads={ac[2]}")

# Write the IDs to a file for the fix script
with open("bad_car_brand_children.txt", "w") as f:
    f.write(",".join(str(x) for x in all_to_delete))

print(f"\nWrote {len(all_to_delete)} IDs to bad_car_brand_children.txt")

conn.close()

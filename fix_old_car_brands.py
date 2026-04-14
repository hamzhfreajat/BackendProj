"""
Fix car brand subcategories:
1. Move Honda models from old Hyundai (1011) to Honda (101122)
2. Delete old brand 1011 (new Hyundai 101124 has correct models)
3. Delete old brands 1012-1017 and move their models to correct new brands
4. Reassign any ads from old brand models to new brand equivalents
"""
import psycopg
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# ============================================================
# STEP 1: Fix Honda models under old Hyundai (1011) 
# Move them to Honda (101122)
# ============================================================
print("STEP 1: Moving Honda models from old Hyundai (1011) to Honda (101122)")
cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 1011")
count_before = cur.fetchone()[0]
print(f"  Models under old Hyundai (1011): {count_before}")

cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 101122")
honda_before = cur.fetchone()[0]
print(f"  Models under Honda (101122) before: {honda_before}")

# Move all models from 1011 to 101122
cur.execute("UPDATE categories SET parent_id = 101122 WHERE parent_id = 1011")
moved = cur.rowcount
print(f"  Moved {moved} models to Honda (101122)")

cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 101122")
honda_after = cur.fetchone()[0]
print(f"  Models under Honda (101122) after: {honda_after}")

# ============================================================
# STEP 2: Map old brands to their new equivalents & move models
# ============================================================
print("\nSTEP 2: Moving models from old brands to new equivalents")

# Old brand -> New equivalent mapping
# We need to find or create new equivalents for 1012-1017
old_to_new = {}

# Toyota (1012) - check if there's a new "تويوتا" brand
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND name LIKE '%تويوتا%'")
row = cur.fetchone()
if row:
    old_to_new[1012] = row[0]
    print(f"  Toyota (1012) -> {row[1]} ({row[0]})")
else:
    # Check by slug
    cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND slugs::text LIKE '%toyota%'")
    row = cur.fetchone()
    if row:
        old_to_new[1012] = row[0]
        print(f"  Toyota (1012) -> {row[1]} ({row[0]}) [by slug]")

# Kia (1013)
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND (name LIKE '%كيا%' OR slugs::text LIKE '%kia%')")
row = cur.fetchone()
if row:
    old_to_new[1013] = row[0]
    print(f"  Kia (1013) -> {row[1]} ({row[0]})")

# Ford (1014)
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND (name LIKE '%فورد%' OR slugs::text LIKE '%ford%')")
row = cur.fetchone()
if row:
    old_to_new[1014] = row[0]
    print(f"  Ford (1014) -> {row[1]} ({row[0]})")

# Nissan (1015)
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND (name LIKE '%نيسان%' OR slugs::text LIKE '%nissan%')")
row = cur.fetchone()
if row:
    old_to_new[1015] = row[0]
    print(f"  Nissan (1015) -> {row[1]} ({row[0]})")

# Mitsubishi (1016)
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND (name LIKE '%ميتسوبيشي%' OR slugs::text LIKE '%mitsubishi%')")
row = cur.fetchone()
if row:
    old_to_new[1016] = row[0]
    print(f"  Mitsubishi (1016) -> {row[1]} ({row[0]})")

# Chinese cars (1017) - models need to be split among MG, BYD, Changan, Geely
# For now, we'll need to handle this specially

print(f"\n  Found new equivalents for {len(old_to_new)} out of 6 old brands (excluding Chinese)")

# For brands that DON'T have new equivalents, we need to CREATE them
if 1012 not in old_to_new:
    # Create new Toyota brand
    cur.execute("""INSERT INTO categories (name, parent_id, slugs, order_index) 
                   VALUES ('تويوتا', 101, '{"ar": ["تويوتا"], "en": ["toyota"]}', 0) 
                   RETURNING id""")
    new_id = cur.fetchone()[0]
    old_to_new[1012] = new_id
    print(f"  CREATED new Toyota brand: {new_id}")

if 1013 not in old_to_new:
    cur.execute("""INSERT INTO categories (name, parent_id, slugs, order_index) 
                   VALUES ('كيا', 101, '{"ar": ["كيا"], "en": ["kia"]}', 0) 
                   RETURNING id""")
    new_id = cur.fetchone()[0]
    old_to_new[1013] = new_id
    print(f"  CREATED new Kia brand: {new_id}")

if 1014 not in old_to_new:
    cur.execute("""INSERT INTO categories (name, parent_id, slugs, order_index) 
                   VALUES ('فورد', 101, '{"ar": ["فورد"], "en": ["ford"]}', 0) 
                   RETURNING id""")
    new_id = cur.fetchone()[0]
    old_to_new[1014] = new_id
    print(f"  CREATED new Ford brand: {new_id}")

if 1015 not in old_to_new:
    cur.execute("""INSERT INTO categories (name, parent_id, slugs, order_index) 
                   VALUES ('نيسان', 101, '{"ar": ["نيسان"], "en": ["nissan"]}', 0) 
                   RETURNING id""")
    new_id = cur.fetchone()[0]
    old_to_new[1015] = new_id
    print(f"  CREATED new Nissan brand: {new_id}")

if 1016 not in old_to_new:
    cur.execute("""INSERT INTO categories (name, parent_id, slugs, order_index) 
                   VALUES ('ميتسوبيشي', 101, '{"ar": ["ميتسوبيشي"], "en": ["mitsubishi"]}', 0) 
                   RETURNING id""")
    new_id = cur.fetchone()[0]
    old_to_new[1016] = new_id
    print(f"  CREATED new Mitsubishi brand: {new_id}")

# ============================================================
# STEP 3: Move models from old brands to new equivalents
# ============================================================
print("\nSTEP 3: Moving models from old brands to new equivalents")
for old_id, new_id in old_to_new.items():
    # Check if the new brand already has models
    cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = %s", (new_id,))
    existing_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = %s", (old_id,))
    old_count = cur.fetchone()[0]
    
    if old_count > 0:
        if existing_count > 0:
            # New brand already has models - delete old ones to avoid duplicates
            print(f"  Brand {old_id}: New equivalent ({new_id}) already has {existing_count} models. Deleting {old_count} old models.")
            cur.execute("DELETE FROM categories WHERE parent_id = %s", (old_id,))
        else:
            # New brand has no models - move old ones there
            cur.execute("UPDATE categories SET parent_id = %s WHERE parent_id = %s", (new_id, old_id))
            print(f"  Moved {old_count} models from {old_id} to {new_id}")

# ============================================================
# STEP 4: Handle Chinese cars (1017) - split models among brands
# ============================================================
print("\nSTEP 4: Handling Chinese cars (1017)")
cur.execute("SELECT id, name FROM categories WHERE parent_id = 1017 ORDER BY name")
chinese_models = cur.fetchall()
print(f"  Total models under Chinese cars (1017): {len(chinese_models)}")

# Map model names to their correct new brands
mg_brand = None
byd_brand = None
changan_brand = None
geely_brand = None
jili_brand = None

# Find the new Chinese brand IDs
for name_pattern, brand_slug in [('ام جي', 'mg'), ('بي واي دي', 'byd'), ('شانجان', 'changan'), ('جيلي', 'geely')]:
    cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 AND id >= 101000 AND (name LIKE %s OR slugs::text LIKE %s)", 
                (f'%{name_pattern}%', f'%{brand_slug}%'))
    row = cur.fetchone()
    if row:
        print(f"  Found new brand: {row[1]} ({row[0]})")
        if brand_slug == 'mg':
            mg_brand = row[0]
        elif brand_slug == 'byd':
            byd_brand = row[0]
        elif brand_slug == 'changan':
            changan_brand = row[0]
        elif brand_slug == 'geely':
            geely_brand = row[0]

# Move MG models
if mg_brand:
    mg_moved = 0
    for mid, mname in chinese_models:
        if mname.startswith('MG ') or mname in ('Cyberster', 'Pilot', 'Rakan', 'T60', 'Whale', 'Other'):
            if mname.startswith('MG '):
                cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (mg_brand, mid))
                mg_moved += 1
    print(f"  Moved {mg_moved} MG models to {mg_brand}")

# Move BYD models
if byd_brand:
    byd_names = ['Atto 3', 'Destroyer 05', 'Dolphin', 'E2', 'E3', 'E6', 'F0', 'F3', 'F3R', 'F5', 'F6', 'F7',
                 'G3', 'Han', 'Leopard 5', 'Leopard 7', 'Leopard 8', 'Qin', 'S6', 'Seagull', 'Seal', 'Shark 6',
                 'Song L', 'Song Max', 'Song Plus', 'Song Pro', 'Tang', 'Yuan']
    byd_moved = 0
    for mid, mname in chinese_models:
        if mname in byd_names:
            cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (byd_brand, mid))
            byd_moved += 1
    print(f"  Moved {byd_moved} BYD models to {byd_brand}")

# Move Geely models
if geely_brand:
    geely_names = ['Azkarra', 'CK', 'Coolray', 'EC7', 'EC8', 'Emgrand', 'GC2', 'GC5', 'GC6', 'GC7',
                   'Geometry C', 'Geometry E', 'GX2', 'GX3 Pro', 'Imperial', 'LC', 'Maple Leaf 60s', 'MK',
                   'Monjaro', 'Okavango', 'Radar', 'S5', 'SC7', 'Starray', 'Tugella']
    geely_moved = 0
    for mid, mname in chinese_models:
        if mname in geely_names:
            cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (geely_brand, mid))
            geely_moved += 1
    print(f"  Moved {geely_moved} Geely models to {geely_brand}")

# Move Changan models
if changan_brand:
    changan_names = ['Alsvin', 'Benni', 'Chana', 'Cosmos', 'CS15', 'CS35', 'CS75', 'CS85', 'CS95',
                     'CX20', 'CX30', 'CX70', 'Deepal', 'E-Star', 'Eado', 'Eado DT', 'Eado EV', 'Eado XT',
                     'Hunter', 'Lumin', 'Sania', 'SL03', 'UNI-K', 'UNI-S', 'UNI-T', 'UNI-V', 'V3', 'V7', 'X7']
    changan_moved = 0
    for mid, mname in chinese_models:
        if mname in changan_names:
            cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (changan_brand, mid))
            changan_moved += 1
    print(f"  Moved {changan_moved} Changan models to {changan_brand}")

# Check remaining models under 1017
cur.execute("SELECT id, name FROM categories WHERE parent_id = 1017 ORDER BY name")
remaining = cur.fetchall()
print(f"\n  Remaining under 1017 after splitting: {len(remaining)}")
for mid, mname in remaining:
    print(f"    [{mid}] {mname}")

# Delete remaining "Other" entries and the brand itself
if remaining:
    for mid, mname in remaining:
        if mname == 'Other':
            cur.execute("DELETE FROM categories WHERE id = %s", (mid,))
            print(f"  Deleted 'Other' entry [{mid}]")
    
    # Also move remaining non-categorized MG-related models
    cur.execute("SELECT id, name FROM categories WHERE parent_id = 1017 ORDER BY name")
    still_remaining = cur.fetchall()
    if still_remaining and mg_brand:
        for mid, mname in still_remaining:
            # Move remaining to MG as fallback (they're MG models like Pilot, Rakan, etc.)
            cur.execute("UPDATE categories SET parent_id = %s WHERE id = %s", (mg_brand, mid))
        print(f"  Moved {len(still_remaining)} remaining models to MG brand")

# ============================================================
# STEP 5: Reassign ads from old brands to new brands
# ============================================================
print("\nSTEP 5: Checking and reassigning ads")
for old_id in [1011, 1012, 1013, 1014, 1015, 1016, 1017]:
    cur.execute("SELECT COUNT(*) FROM ads WHERE category_id = %s", (old_id,))
    count = cur.fetchone()[0]
    if count > 0:
        new_id = old_to_new.get(old_id)
        if new_id:
            cur.execute("UPDATE ads SET category_id = %s WHERE category_id = %s", (new_id, old_id))
            print(f"  Moved {count} ads from {old_id} to {new_id}")
        else:
            print(f"  WARNING: {count} ads on old brand {old_id} but no new equivalent!")

# ============================================================
# STEP 6: Delete old brand categories
# ============================================================
print("\nSTEP 6: Deleting old brand categories")
for old_id in [1011, 1012, 1013, 1014, 1015, 1016, 1017]:
    # Check if it still has children
    cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = %s", (old_id,))
    remaining_children = cur.fetchone()[0]
    if remaining_children > 0:
        print(f"  WARNING: Brand {old_id} still has {remaining_children} children! Skipping delete.")
    else:
        cur.execute("DELETE FROM categories WHERE id = %s", (old_id,))
        print(f"  Deleted old brand {old_id}")

# ============================================================
# STEP 7: Do the same for rental cars (102) old brands
# ============================================================
print("\nSTEP 7: Checking old brands under rental cars (102)")
cur.execute("SELECT id, name FROM categories WHERE parent_id = 102 AND id < 10000 ORDER BY id")
old_rental_brands = cur.fetchall()
if old_rental_brands:
    print(f"  Found {len(old_rental_brands)} old rental brands:")
    for rid, rname in old_rental_brands:
        print(f"    [{rid}] {rname}")
else:
    print("  No old rental brands found")

# ============================================================
# STEP 8: Verify final state
# ============================================================
print("\nSTEP 8: Verification")
cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 101")
total_brands = cur.fetchone()[0]
print(f"  Total brands under 'cars for sale' (101): {total_brands}")

# Check no old brands remain
cur.execute("SELECT id, name FROM categories WHERE id BETWEEN 1011 AND 1017")
old_remaining = cur.fetchall()
if old_remaining:
    print(f"  WARNING: Old brands still exist: {old_remaining}")
else:
    print("  All old brands (1011-1017) removed successfully!")

# Check Honda has models
cur.execute("SELECT COUNT(*) FROM categories WHERE parent_id = 101122")
honda_models = cur.fetchone()[0]
print(f"  Honda (101122) now has {honda_models} models")

# Check no orphan ads
cur.execute("SELECT COUNT(*) FROM ads WHERE category_id NOT IN (SELECT id FROM categories)")
orphans = cur.fetchone()[0]
print(f"  Orphan ads (no valid category): {orphans}")

# Commit
conn.commit()
print("\n=== ALL CHANGES COMMITTED SUCCESSFULLY ===")

conn.close()

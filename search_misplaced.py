"""Search for misplaced categories (medical, clothing, etc.) under any car brand."""
import psycopg

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

search_terms = ['ادوية', 'أدوية', 'وقاية', 'مستلزمات طبية', 'ملابس', 'خدمات طبية', 'تجميل', 'إكسسوارات']

for term in search_terms:
    cur.execute(
        "SELECT c.id, c.name, c.parent_id, p.name as parent_name "
        "FROM categories c "
        "LEFT JOIN categories p ON c.parent_id = p.id "
        "WHERE c.name LIKE %s", 
        (f'%{term}%',)
    )
    rows = cur.fetchall()
    if rows:
        print(f'Search: {term}')
        for r in rows:
            print(f'  [{r[0]}] {r[1]} -> parent [{r[2]}] {r[3]}')
        print()

# Also check: are there any non-car categories that have a car brand as parent?
print("\n\nChecking ALL children of car brands for non-car model names...")
# Get all brand IDs under 101
cur.execute("SELECT id, name FROM categories WHERE parent_id = 101 ORDER BY id")
brands = cur.fetchall()

non_car_keywords = ['طب', 'صح', 'دوا', 'ملابس', 'حذ', 'عطر', 'مجوهر', 'ساعا', 'حقيب', 'تجميل', 'مكياج', 'كتب', 'رياض', 'لعب']

for bid, bname in brands:
    cur.execute("SELECT id, name FROM categories WHERE parent_id = %s ORDER BY name", (bid,))
    children = cur.fetchall()
    for cid, cname in children:
        for kw in non_car_keywords:
            if kw in cname:
                print(f"  SUSPICIOUS: [{cid}] '{cname}' under brand [{bid}] '{bname}'")
                break

print("\nDone.")
conn.close()

import psycopg
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = psycopg.connect('host=localhost port=5432 dbname=open user=postgres password=123456')
cur = conn.cursor()

# Get all categories
cur.execute("SELECT id, parent_id, name, description, icon_name, color_hex, tag, slugs FROM categories ORDER BY id ASC")
rows = cur.fetchall()

print(f"Total rows in DB: {len(rows)}")

out = []
out.append("CATEGORIES = [\n")

for r in rows:
    # Format the slugs correctly
    slugs = "None"
    if r[7] is not None:
        import json
        slugs = json.dumps(r[7], ensure_ascii=False)
        
    tag = r[6]
    tag_str = f'"{tag}"' if tag else "None"
    
    desc = r[3]
    desc_str = f'"{desc}"' if desc else "None"
    
    icon = r[4]
    icon_str = f'"{icon}"' if icon else "None"
    
    color = r[5]
    color_str = f'"{color}"' if color else "None"
    
    parent = r[1]
    parent_str = str(parent) if parent else "None"
    
    out.append(f'    ({r[0]}, {parent_str}, "{r[2]}", {desc_str}, {icon_str}, {color_str}, {tag_str}, {slugs}),\n')

out.append("]\n\n")

with open('footer.txt', 'r', encoding='utf-8') as f:
    footer = f.read()

out.append(footer)

import codecs
with codecs.open('seed_categories_perfect.py', 'w', encoding='utf-8') as f:
    f.writelines(out)

print("Created seed_categories_perfect.py with ALL data from DB!")
conn.close()

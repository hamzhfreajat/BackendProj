import sqlite3
import json

conn = sqlite3.connect('classifieds.db')
c = conn.cursor()

c.execute("SELECT city, COUNT(*) FROM ads WHERE region = 'أخرى' GROUP BY city")
rows = c.fetchall()
print("Counts per city:")
for r in rows:
    print(f"{r[0]}: {r[1]}")

c.execute("SELECT city, description FROM ads WHERE region = 'أخرى'")
ads = c.fetchall()

result = {}
for city, desc in ads:
    if city not in result:
        result[city] = []
    result[city].append(desc)

with open('all_others_descriptions.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Total ads extracted: {len(ads)}")

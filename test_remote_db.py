import os
import json
import psycopg2

conn = psycopg2.connect(
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK',
    host='178.104.204.148',
    port=9000
)
cur = conn.cursor()

# Get the latest ad inserted
cur.execute('SELECT id, attributes, image_url, created_at FROM ads ORDER BY id DESC LIMIT 5;')
ads = cur.fetchall()
for ad in ads:
    print(f'Ad ID: {ad[0]}, Created At: {ad[3]}')
    print(f'Main Image URL: {ad[2]}')
    attrs = ad[1] if ad[1] else {}
    print(f'Attributes Image URLs: {attrs.get("image_urls", [])}')
    print('-' * 40)
    
conn.close()

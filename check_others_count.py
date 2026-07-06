import psycopg2

conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM ads WHERE location LIKE '%أخرى%'")
count = cur.fetchone()[0]
print(f"Total ads remaining in Others: {count}")
conn.close()

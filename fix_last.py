import psycopg2
conn = psycopg2.connect(host='178.104.204.148', port=9000, dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
cur = conn.cursor()
cur.execute("UPDATE ads SET location = 'عمان, أخرى' WHERE location = 'عمان'")
conn.commit()
conn.close()

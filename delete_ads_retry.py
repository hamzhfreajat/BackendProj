import psycopg
import time
import sys

URL = "postgresql://postgres:p2j9ggm6cWLAhhVTsbNzYFqK@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q"

for i in range(10):
    try:
        print(f"Attempt {i+1} to connect...")
        with psycopg.connect(URL) as conn:
            with conn.cursor() as cur:
                # Find the ads
                cur.execute("SELECT id FROM ads WHERE ads::text LIKE '%0772422663%'")
                rows = cur.fetchall()
                ids = [r[0] for r in rows]
                if ids:
                    cur.execute("DELETE FROM ads WHERE id = ANY(%s)", (ids,))
                    conn.commit()
                print(f"Deleted {len(ids)} ads with number 0772422663")
        sys.exit(0)
    except psycopg.OperationalError as e:
        print(f"Error: {e}")
        time.sleep(2)

print("Failed after 10 attempts.")
sys.exit(1)

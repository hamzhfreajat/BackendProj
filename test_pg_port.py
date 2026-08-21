import psycopg2

def fix():
    try:
        conn = psycopg2.connect(
            host="178.104.204.148",
            port=9000,
            dbname="cmnynjgg90003aumlerff4j9q",
            user="postgres",
            password="p2j9ggm6cWLAhhVTsbNzYFqK"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Adding wallet_balance...")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_balance DECIMAL(10, 2) DEFAULT 0.00;")
        
        print("Done!")
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    fix()

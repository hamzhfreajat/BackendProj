import psycopg2
try:
    conn = psycopg2.connect(host='178.104.204.148', port='9000', dbname='cmnynjgg90003aumlerff4j9q', user='postgres', password='p2j9ggm6cWLAhhVTsbNzYFqK')
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(id) FROM users")
    users_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(id) FROM user_device_tokens")
    devices_count = cur.fetchone()[0]
    
    print(f"Registered Users: {users_count}")
    print(f"Device Tokens (Installs that allowed notifications): {devices_count}")
except Exception as e:
    print('ERROR:', e)

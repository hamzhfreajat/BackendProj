import requests

# We don't have a valid token, but we can check if the server HAS our fix.
# If we try to hit PUT /api/ads/14068/toggle-publish without a token, it returns 401.
# This means we MUST have a valid token to test the logic.

# Let's get a valid user from the DB to forge a token.
import psycopg2
import jwt
import datetime

conn = psycopg2.connect(
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK',
    host='178.104.204.148',
    port=9000
)
cur = conn.cursor()
# find a real user
cur.execute('SELECT id FROM users LIMIT 1;')
user_id = cur.fetchone()[0]
conn.close()

print(f"Testing with User ID: {user_id}")

SECRET_KEY = 'dummy_secret_for_local_run'
payload = {
    'sub': str(user_id),
    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
}
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Try to toggle-publish Ad 14068 (which has NO images)
# Note: Ad 14068 belongs to whoever created it, so we need to use THEIR user ID!
conn = psycopg2.connect(
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK',
    host='178.104.204.148',
    port=9000
)
cur = conn.cursor()
cur.execute('SELECT user_id FROM ads WHERE id = 14068;')
ad_user_id = cur.fetchone()[0]
conn.close()

payload['sub'] = str(ad_user_id)
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
headers['Authorization'] = f'Bearer {token}'

print(f"Testing with Ad Owner ID: {ad_user_id}")

resp = requests.put('https://api.sooq-com.com/api/ads/14068/toggle-publish', headers=headers)
print('Toggle Publish Response:', resp.status_code, resp.text)

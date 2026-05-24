import urllib.request
import json

url = "https://api.sooq-com.com/api/categories?parent_id=10310"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json'
}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Count: {len(data)}")
        if len(data) > 0:
            print("First item:", data[0]['name'])
except Exception as e:
    print("Error:", e)

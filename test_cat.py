import urllib.request
import json

url = "https://api.sooq-com.com/api/categories?parent_id=10310"
req = urllib.request.Request(url)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print("Error:", e)

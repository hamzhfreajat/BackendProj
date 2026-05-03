import requests

resp = requests.get("http://localhost:8000/api/ads?limit=1")
if resp.status_code == 200:
    data = resp.json()
    if data:
        print("Owner data:", data[0].get("owner"))
else:
    print("Error:", resp.status_code, resp.text)

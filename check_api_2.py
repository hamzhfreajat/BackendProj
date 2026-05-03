import requests

resp = requests.get("http://localhost:8000/api/ads?limit=5")
if resp.status_code == 200:
    data = resp.json()
    for i, ad in enumerate(data):
        print(f"Ad {ad['id']} owner:", ad.get("owner", {}).get("full_name"), ad.get("owner", {}).get("username"))
else:
    print("Error:", resp.status_code, resp.text)

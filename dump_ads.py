import requests
import json

resp = requests.get("http://localhost:8000/api/ads?limit=1")
with open("ad_response.json", "w", encoding="utf-8") as f:
    json.dump(resp.json(), f, ensure_ascii=False, indent=2)

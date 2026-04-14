import requests

try:
    url = "https://api.opensooq.com/v2.1/search/sub-categories?parent_id=71"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    print("Honda (71) status:", r.status_code)
    print(r.text[:500])
except Exception as e:
    print(e)

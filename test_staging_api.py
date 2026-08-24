import requests
try:
    r = requests.get('https://staging.sooq-com.com/api/ads/?search=5000000')
    if r.status_code == 200:
        for ad in r.json():
            print(f"Ad: {ad.get('id')}, cpc_bid: {ad.get('cpc_bid')}, price: {ad.get('price')}")
    else:
        print("Failed:", r.status_code)
except Exception as e:
    print("Error:", e)

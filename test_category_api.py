import requests
try:
    r2 = requests.get('https://staging.sooq-com.com/api/ads/?category_id=10301')
    if r2.status_code == 200:
        ads = r2.json()
        count = 0
        for a in ads:
            if a.get('cpc_bid') and a.get('cpc_bid') > 0:
                print(f"Ad {a.get('id')} has cpc_bid: {a.get('cpc_bid')}")
                count += 1
        print("Total ads with cpc_bid > 0:", count)
    else:
        print("Error:", r2.status_code)
except Exception as e:
    print("Exception:", e)

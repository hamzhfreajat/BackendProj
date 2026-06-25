import urllib.request, json, ssl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
url = 'https://api.sooq-com.com/api/scraping-logs?page=1&limit=20&sort_by=group_name&sort_desc=false'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode())
        if 'items' in data:
            for item in data['items']:
                print(f"#{item['id']} {item['group_name']}")
        else:
            print('No items key')
except Exception as e:
    print('Error:', e)

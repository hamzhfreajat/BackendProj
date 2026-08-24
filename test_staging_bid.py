import urllib.request
import json

import ssl

def test():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://staging.sooq-com.com/api/ads/35517/bid"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MyIsImVtYWlsIjoiaGFtemhnMjAyMEBnbWFpbC5jb20iLCJleHAiOjE4MTg4NDg0ODl9.vVaMqUkTLXN0QIRdzaF9yjI9cKt9DYWZEU_UFs9g0z0",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    data = json.dumps({"cpc_bid": 0.15}).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            print("HTTP STATUS:", response.status)
            body = response.read()
            with open("test_resp.json", "wb") as f:
                f.write(body)
            print("RESPONSE SAVED TO test_resp.json")
    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
        print("ERROR RESPONSE:", e.read().decode())
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    test()

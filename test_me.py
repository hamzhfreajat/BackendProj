import urllib.request
import json
import ssl

def test():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://staging.sooq-com.com/api/auth/me"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MyIsImVtYWlsIjoiaGFtemhnMjAyMEBnbWFpbC5jb20iLCJleHAiOjE4MTg4NDg0ODl9.vVaMqUkTLXN0QIRdzaF9yjI9cKt9DYWZEU_UFs9g0z0",
        "User-Agent": "Mozilla/5.0"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            print("HTTP STATUS:", response.status)
            body = response.read().decode()
            print("RESPONSE:", body)
    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
        print("ERROR RESPONSE:", e.read().decode())
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    test()

import urllib.request
import ssl

def test():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    url = "https://staging.sooq-com.com/api/wallet/nonexistent_endpoint_123"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    req = urllib.request.Request(url, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            print("HTTP STATUS:", response.status)
            print("RESPONSE:", response.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP ERROR:", e.code)
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    test()

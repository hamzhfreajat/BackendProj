import urllib.request
import json

def test():
    urls = [
        "http://5.45.131.27:8081/api/ads",
        "http://5.45.131.27/api/ads",
        "https://classifieds-app-staging.optimizasolutions.com/api/ads"
    ]
    for url in urls:
        print(f"Testing {url}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                print("Status:", response.status)
                data = json.loads(response.read().decode())
                print("Response keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        except Exception as e:
            print("Failed:", e)

if __name__ == "__main__":
    test()

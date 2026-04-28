import requests
import urllib.parse

def test_api():
    # Test count API
    url = f"http://127.0.0.1:8000/api/ads/count?location={urllib.parse.quote('عمان')}&location={urllib.parse.quote('عبدون')}"
    res = requests.get(url)
    print(f"Count for Amman, Abdoun: {res.text}")

    # Test ads API
    url = f"http://127.0.0.1:8000/api/ads?location={urllib.parse.quote('عمان')}&location={urllib.parse.quote('عبدون')}"
    res = requests.get(url)
    try:
        ads = res.json()
        print(f"Ads returned for Amman, Abdoun: {len(ads)}")
    except:
        print("Failed to decode JSON")

if __name__ == "__main__":
    test_api()

import requests

def test_localtunnel():
    url = "https://all-fans-vanish.loca.lt/api/ads/count"
    try:
        res = requests.get(url, headers={"Bypass-Tunnel-Reminder": "true"})
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_localtunnel()

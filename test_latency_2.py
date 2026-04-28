import time
import requests

def test_api():
    start = time.time()
    res = requests.get("http://localhost:8000/api/ads/count?location=عمان")
    end = time.time()
    print(f"Time for Count Amman: {end - start:.3f} seconds")

    start = time.time()
    res = requests.get("http://localhost:8000/api/ads?location=عمان&sort_by=oldest")
    end = time.time()
    print(f"Time for Ads Amman (Oldest): {end - start:.3f} seconds")

    start = time.time()
    res = requests.get("http://localhost:8000/api/ads?location=عمان&sort_by=recommended")
    end = time.time()
    print(f"Time for Ads Amman (Recommended): {end - start:.3f} seconds")

if __name__ == "__main__":
    test_api()

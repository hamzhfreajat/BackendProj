import time
import requests

def test_api():
    start = time.time()
    res = requests.get("http://127.0.0.1:8000/api/ads/count?location=عمان")
    end = time.time()
    print(f"Time for Count Amman 127: {end - start:.3f} seconds")

if __name__ == "__main__":
    test_api()

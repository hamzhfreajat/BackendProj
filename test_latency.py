import time
import requests

def test_api():
    start = time.time()
    res = requests.get("http://localhost:8000/api/ads?location=عمان&location=أخرى")
    end = time.time()
    print(f"Time for Amman, Other: {end - start:.3f} seconds")
    print(f"Status: {res.status_code}")

    start = time.time()
    res = requests.get("http://localhost:8000/api/ads?location=العقبة")
    end = time.time()
    print(f"Time for Aqaba: {end - start:.3f} seconds")
    print(f"Status: {res.status_code}")

if __name__ == "__main__":
    test_api()

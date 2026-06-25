import requests

def test():
    res = requests.post("http://localhost:8000/api/facebook/manual-publish", json={
        "region_name": "تلاع العلي",
        "count": 5,
        "custom_text": "Integration test for images"
    })
    print(res.status_code)
    print(res.text)

if __name__ == "__main__":
    test()

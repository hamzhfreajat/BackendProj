import requests
import json
import uuid

BASE_URL = "https://staging.sooq-com.com/api"
# BASE_URL = "http://127.0.0.1:8080/api"

def main():
    # 1. Create a user
    phone = f"079{str(uuid.uuid4().int)[:7]}"
    print(f"Creating user {phone}...")
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "phone": phone,
        "password": "password123",
        "name": "Test User"
    })
    if resp.status_code != 200:
        print("Register failed:", resp.text)
        return
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check balance
    resp = requests.get(f"{BASE_URL}/users/me/profile", headers=headers)
    print("User profile:", resp.text)

    # 2. Create an ad
    resp = requests.post(f"{BASE_URL}/ads", headers=headers, json={
        "title": "Test Ad",
        "desc": "Test Description",
        "price": 100,
        "currency": "JOD",
        "category_id": 1,
        "location_id": 1
    })
    if resp.status_code != 200:
        print("Ad creation failed:", resp.text)
        # Try to get existing categories to find a valid category_id
        cats = requests.get(f"{BASE_URL}/categories").json()
        if not cats: return
        cat_id = cats[0]['id']
        resp = requests.post(f"{BASE_URL}/ads", headers=headers, json={
            "title": "Test Ad",
            "desc": "Test Description",
            "price": 100,
            "currency": "JOD",
            "category_id": cat_id,
            "location_id": 1
        })
        if resp.status_code != 200:
            print("Ad creation failed again:", resp.text)
            return

    ad_id = resp.json().get("id")
    print(f"Created ad {ad_id}")

    # 3. Try to bid
    resp = requests.post(f"{BASE_URL}/ads/{ad_id}/bid", headers=headers, json={
        "cpc_bid": 0.10
    })
    print(f"Bid response (Status {resp.status_code}):", resp.text)

if __name__ == "__main__":
    main()

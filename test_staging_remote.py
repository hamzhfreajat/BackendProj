import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

def test():
    if not SECRET_KEY:
        print("No secret key!")
        return

    to_encode = {"sub": "63", "email": "hamzhg2020@gmail.com"}
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to bid on ad 35517 (the one from the user's logs)
    url = "https://staging.sooq-com.com/api/ads/35517/bid"
    print(f"Testing {url}...")
    resp = requests.post(url, headers=headers, json={"cpc_bid": 0.07})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    test()

import requests

API_KEY = "ea25ec8a68msh72ee5bb2b1aa226p148c24jsncc9d73f0feac"
TARGET_URL = "https://www.facebook.com/groups/476046146252156"

# List of popular RapidAPI Facebook Scraper Hosts
HOSTS = [
    "facebook-scraper3.p.rapidapi.com",
    "facebook-scraper2.p.rapidapi.com",
    "facebook-data-scraper.p.rapidapi.com",
    "facebook-scraper.p.rapidapi.com",
    "fresh-facebook-scraper.p.rapidapi.com",
    "facebook-groups-scraper.p.rapidapi.com",
    "facebook-api.p.rapidapi.com",
    "fb-scraper.p.rapidapi.com",
    "fb-scraper1.p.rapidapi.com",
    "social-media-scraper.p.rapidapi.com",
    "facebook-scraper-api.p.rapidapi.com",
    "taskagi-facebook-scraper.p.rapidapi.com"
]

print("Testing RapidAPI Key against known hosts...")

for host in HOSTS:
    url = f"https://{host}/"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": host
    }
    
    try:
        # A simple GET request to the root or a health endpoint
        response = requests.get(url, headers=headers, timeout=5)
        
        # If the API key is not subscribed, RapidAPI consistently returns a specific message or 403 Forbidden.
        # "You are not subscribed" is the typical rejection.
        if "not subscribed" not in response.text.lower() and response.status_code != 403:
            print(f"[SUCCESS] Key is active or valid for: {host}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            print("---")
        else:
            # print(f"[FAIL] {host}")
            pass
            
    except Exception as e:
        print(f"[ERROR] {host} - {str(e)}")

print("Done.")

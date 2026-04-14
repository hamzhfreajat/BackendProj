import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
    'country': 'jo',
    'source': '1',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI4MTIyMzMiLCJleHAiOjE3NzQ0MjUyMjR9.QgR1yL3LVZ21Js7nnKuHN7oiHDVVzlZt7Ojm7tHR1XY'
}

url = "https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpSmartWatchesBrand_child&type=add-post&workflowId=401126&draftId=5cc5b3eb-b97c-450f-99af-816cf7d96770&stepId=post_previewStep&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1&cpSmartWatchesBrand=19371"

r = requests.get(url, headers=HEADERS)
print("Status Code:", r.status_code)
try:
    print(r.json())
except:
    print(r.text)

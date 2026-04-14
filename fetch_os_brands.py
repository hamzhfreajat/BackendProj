import requests
import json

url1 = "https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpPhones_Brand&type=add-post&workflowId=401122&draftId=5cc5b3eb-b97c-450f-99af-816cf7d96770&stepId=post_previewStep&expand=remaining_edit_counter,media,post.overLimitType,post.isOverLimit&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1"
url2 = "https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpPhones_Brand_child&type=add-post&workflowId=401122&draftId=5cc5b3eb-b97c-450f-99af-816cf7d96770&stepId=post_previewStep&expand=remaining_edit_counter,media,post.overLimitType,post.isOverLimit&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
    'country': 'jo',
    'source': '1',
    'Source': '1',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI4MTIyMzMiLCJleHAiOjE3NzQ0MjUyMjR9.QgR1yL3LVZ21Js7nnKuHN7oiHDVVzlZt7Ojm7tHR1XY'
}

r1 = requests.get(url1, headers=headers)
with open('brands.json', 'w', encoding='utf-8') as f:
    f.write(r1.text)
print("brands status:", r1.status_code)
print("brands text:", r1.text[:200])

r2 = requests.get(url2, headers=headers)
with open('sub_brands.json', 'w', encoding='utf-8') as f:
    f.write(r2.text)
print("sub_brands status:", r2.status_code)
print("sub_brands text:", r2.text[:200])

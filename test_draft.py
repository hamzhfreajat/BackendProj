import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# The token the user just gave me today:
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI2Mzk0MTIiLCJleHAiOjE3NzU0ODUyODl9.EVhbrqh_tprAGUmYCuN6EUghN0FhLcJ2EvISa3ry0WA"
draft_id = "d94c8dae-f52f-48e2-9b95-7d0cacd83f51"

save_data_url = f"https://api.opensooq.com/vertical/forms/v1/add-post/save-data/425350/cpMake_Motorbike?draftId={draft_id}&stepId=post_previewStep&country=jo&source=1"
widget_url = f"https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpMake_Motorbike_child&type=add-post&workflowId=425350&draftId={draft_id}&stepId=post_previewStep&country=jo&source=1"

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0',
    'Country': 'jo',
    'Source': '1'
}

print("Testing Honda (ID: 71)...")
# 1. Update draft
payload = {"value": "71"}
r_save = requests.post(save_data_url, headers=headers, json=payload)
print(f"Save-data status: {r_save.status_code}")

# 2. Fetch widget for children
r_child = requests.get(widget_url, headers=headers)
print(f"Widget status: {r_child.status_code}")
data = r_child.json()
if 'result' in data and 'data' in data['result'] and 'values' in data['result']['data']:
    values = data['result']['data']['values']
    print(f"Honda submodels: {len(values)}")
    for v in values[:3]:
        print(v['label'])
else:
    print("Failed to get children.")

import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpMake_Motorbike&type=add-post&workflowId=425350&draftId=d94c8dae-f52f-48e2-9b95-7d0cacd83f51&stepId=post_previewStep&expand=remaining_edit_counter,media,post.overLimitType,post.isOverLimit&cMedium=web_open&cName=direct_web_open&cSource=opensooq&abBucket=3&country=jo&source=1'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI2Mzk0MTIiLCJleHAiOjE3NzU0ODUyODl9.EVhbrqh_tprAGUmYCuN6EUghN0FhLcJ2EvISa3ry0WA',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Country': 'jo',
    'Source': '1'
}

response = requests.get(url, headers=headers)
print('Status:', response.status_code)
if response.status_code == 200:
    data = response.json()
    with open('os_brands.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    values = data.get('result', {}).get('data', {}).get('values', [])
    print(f'Total brands fetched: {len(values)}')
    for v in values[:3]:
        print(f"Brand: {v.get('label')}, ID: {v.get('id')}")

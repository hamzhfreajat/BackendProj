import json
import requests
import time
from database import SessionLocal
from models import Category

def run():
    db = SessionLocal()
    
    print("Deleting old subcategories under 101 (Sale) and 102 (Rent)...")
    db.query(Category).filter(Category.parent_id.in_([101, 102])).delete(synchronize_session=False)
    db.commit()

    with open(r'C:\Users\hfraijat\.gemini\antigravity\brain\696fb396-0dce-4ae5-a16f-7a3bb2cd2761\scratch\brands.json', 'r', encoding='utf-8') as f:
        brands_data = json.load(f)
        
    brands = brands_data['values']
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ar',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiIxMTc5MTU5IiwiZXhwIjoxNzg4ODA4NTgzfQ.YlmpWFRpShJYE75sRQy0S6ySgAc62c2DLiMvC7gTXlA',
        'source': 'desktop',
        'country': 'jo',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36'
    }

    print(f"Loaded {len(brands)} brands. Fetching models...")

    for i, b in enumerate(brands):
        brand_id = b['id']
        brand_name = b['label']
        print(f"[{i+1}/{len(brands)}] Fetching models for ID: ({brand_id})")
        
        url = f"https://api.opensooq.com/vertical/forms/v1/add-post/widget?id=cpModel&cpBrand={brand_id}&type=add-post&workflowId=459672&draftId=f7f7256a-04d0-4c32-8449-d5b41b47a454&stepId=post_previewStep"
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                models = data.get('result', {}).get('data', {}).get('values', [])
            else:
                print(f"Error {resp.status_code} for brand ID {brand_id}")
                models = []
        except Exception as e:
            print(f"Exception fetching brand ID {brand_id}: {e}")
            models = []
            
        # Add to 101 (Sale)
        brand_101 = Category(parent_id=101, name=brand_name)
        db.add(brand_101)
        db.commit() # commit to get brand_101.id
        
        for m in models:
            db.add(Category(parent_id=brand_101.id, name=m['label']))
            
        # Add to 102 (Rent)
        brand_102 = Category(parent_id=102, name=brand_name)
        db.add(brand_102)
        db.commit()
        
        for m in models:
            db.add(Category(parent_id=brand_102.id, name=m['label']))
            
        db.commit()
        time.sleep(0.5)

    print("Finished updating categories!")
    db.close()

if __name__ == '__main__':
    run()

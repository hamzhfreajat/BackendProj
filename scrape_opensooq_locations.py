import requests
import json
import time
import sys
import models
from database import engine, SessionLocal

# --- CONFIGURATION FROM LATEST MESSAGE ---
DRAFT_ID = "7bbd0aa0-5003-45f5-87f7-e1f000ab7d31"
WORKFLOW_ID = "418554"
# Use the token explicitly provided in the latest GET request trace
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdDAiOjE3NzE4MzY0MzQsImF1ZCI6ImRlc2t0b3AiLCJzdWIiOjE0NzMzOTE5LCJybmQiOiI3MzE0MTUiLCJleHAiOjE3NzYwMDMyNjJ9.UjLmFP2d_6AKtfkvmsVn43jr0RX3AddQDRxqQkazBsI"

HEADERS = {
    'abbucket': '3',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ar',
    'authorization': f'Bearer {TOKEN}',
    'country': 'jo',
    'enforce-language': 'ar',
    'origin': 'https://add.opensooq.com',
    'referer': 'https://add.opensooq.com/',
    'release-version': '11.3.0',
    'session-id': '3bffcac4-bd77-4781-baf9-cb446b2a6538',
    'source': 'desktop',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'x-tracking-uuid': '3bffcac4-bd77-4781-baf9-cb446b2a6538'
}

BASE_URL = "https://api.opensooq.com/vertical/forms/v1"
WIDGET_URL = f"{BASE_URL}/add-post/widget?type=add-post&workflowId={WORKFLOW_ID}&draftId={DRAFT_ID}&stepId=post_previewStep"
SAVE_URL = f"{BASE_URL}/add-post/save-data/{WORKFLOW_ID}"

def lg(msg):
    print(msg, flush=True)

def get_options(identifier):
    url = f"{WIDGET_URL}&id={identifier}"
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            if 'result' in data and 'data' in data['result']:
                return data['result']['data'].get('values', [])
    except Exception as e:
        lg(f"GET {identifier} Error: {e}")
    return []

def save_draft_state(identifier, value):
    url = f"{SAVE_URL}/{identifier}?abBucket=3&expand=remaining_edit_counter,media,post.overLimitType,post.isOverLimit&cMedium=web_open&cName=direct_web_open&cSource=opensooq"
    headers = HEADERS.copy()
    headers['content-type'] = 'application/x-www-form-urlencoded'
    
    # Send draftId along with the identifier
    payload = f"draftId={DRAFT_ID}&{identifier}={value}"
    
    try:
        r = requests.post(url, headers=headers, data=payload)
        return r.status_code == 200
    except Exception as e:
        lg(f"POST {identifier} Error: {e}")
        return False

def scrape_and_seed():
    db = SessionLocal()
    
    # 1. Get Governorates
    districts = get_options("districtListIdentifier")
    lg(f"Found {len(districts)} Governorates.")
    
    for dist in districts: # Loop all governorates
        gov_id_opensooq = dist['id']
        gov_name_ar = dist['label']
        lg(f"\nProcessing: {gov_name_ar.encode('utf-8', 'ignore').decode('utf-8')} ({gov_id_opensooq})")
        
        clean_name = gov_name_ar.replace("محافظة ", "").strip()
        local_city = db.query(models.City).filter(models.City.name_ar.like(f"%{clean_name}%")).first()
        if not local_city:
            local_city = models.City(name_en=clean_name, name_ar=clean_name)
            db.add(local_city)
            db.flush()

        # Mutate draft to this Governorate
        success = save_draft_state("districtListIdentifier", gov_id_opensooq)
        if not success:
            lg(f"Failed to save draft for governorate {gov_id_opensooq}")
            continue
        
        time.sleep(0.5)
        
        # 2. Get Directorates
        departments = get_options("departmentListIdentifier")
        
        for dept in departments:
            dept_id_opensooq = dept['id']
            dept_name_ar = dept['label']
            lg(f" -> Saving Directorate: {dept_name_ar.encode('utf-8', 'ignore').decode('utf-8')} ({dept_id_opensooq})")
            
            directorate = db.query(models.Directorate).filter_by(city_id=local_city.id, name_ar=dept_name_ar).first()
            if not directorate:
                directorate = models.Directorate(city_id=local_city.id, name_ar=dept_name_ar)
                db.add(directorate)
            db.flush()
            
            # --- Depth: Villages ---
            success_dept = save_draft_state("departmentListIdentifier", dept_id_opensooq)
            if success_dept:
                time.sleep(0.2)
                villages = get_options("villageListIdentifier")
                for v in villages:
                    v_id = v['id']
                    v_name = v['label']
                    # To keep logs clean, write smaller
                    lg(f"    --> Village: {v_name.encode('utf-8','ignore').decode('utf-8')} ({v_id})")
                    village = db.query(models.Village).filter_by(directorate_id=directorate.id, name_ar=v_name).first()
                    if not village:
                        village = models.Village(directorate_id=directorate.id, name_ar=v_name)
                        db.add(village)
                        db.flush()
                        
                    # --- Depth: Basins (الحوض) ---
                    success_village = save_draft_state("villageListIdentifier", v_id)
                    if success_village:
                        time.sleep(0.2) # sleep to prevent rate limits
                        basins = get_options("hodListIdentifier")
                        for b in basins:
                            b_id = b['id']
                            b_name = b['label']
                            lg(f"      ---> Basin: {b_name.encode('utf-8','ignore').decode('utf-8')} ({b_id})")
                            basin = db.query(models.Basin).filter_by(village_id=village.id, name_ar=b_name).first()
                            if not basin:
                                basin = models.Basin(village_id=village.id, name_ar=b_name)
                                db.add(basin)
                        db.flush()
                    else:
                        lg(f"Failed to save draft for village {v_id}")

            else:
                lg(f"Failed to save draft for directorate {dept_id_opensooq}")
                
            db.commit() # Incremental save

    db.close()
    lg("\nScraping and Seeding Completed Successfully!")

if __name__ == "__main__":
    scrape_and_seed()

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel, Field

# Setup environment
load_dotenv('d:/open/classifieds-app/backend/.env')
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
import models

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No GEMINI_API_KEY found.")
    sys.exit(1)
genai.configure(api_key=api_key)

class PriceExtraction(BaseModel):
    price: float = Field(description="The extracted real price in JOD. Must be a valid realistic price > 99. If no realistic price > 99 is found, return 0.")

def fix_ads():
    db = SessionLocal()
    ads = db.query(models.Ad).filter(models.Ad.price >= 1, models.Ad.price <= 99).all()
    print(f"Found {len(ads)} ads to process.")
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    system_instruction = "You are a data extraction assistant. Read the following ad description. Extract the REAL price (in JOD) for the item being sold (typically a car, apartment, or land). The price MUST be > 99. If the only numbers you see are small (e.g. 'used 1 month', '99% clean', '3 days', '5 years'), then NO real price is mentioned. If no real price > 99 is mentioned, return 0."
    
    updated_count = 0
    deleted_count = 0
    
    for idx, ad in enumerate(ads):
        try:
            desc = ad.description or ad.raw_description or ""
            prompt = f"Description:\n{desc}"
            
            response = model.generate_content(
                system_instruction + "\n\n" + prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=PriceExtraction,
                    temperature=0.0
                )
            )
            
            import json
            res = json.loads(response.text)
            new_price = float(res.get("price", 0))
            
            if new_price > 99:
                print(f"[{idx+1}/{len(ads)}] Updating ad {ad.id} price: {ad.price} -> {new_price}")
                ad.price = new_price
                updated_count += 1
            else:
                print(f"[{idx+1}/{len(ads)}] Deleting ad {ad.id} - no valid real price found. Old price: {ad.price}")
                db.delete(ad)
                deleted_count += 1
                
            # Sleep slightly to avoid hitting rate limits
            import time
            time.sleep(0.5)
                
        except Exception as e:
            print(f"[{idx+1}/{len(ads)}] Error processing ad {ad.id}: {e}")
            
    db.commit()
    print(f"Done! Updated {updated_count} ads, Deleted {deleted_count} ads.")

if __name__ == "__main__":
    fix_ads()

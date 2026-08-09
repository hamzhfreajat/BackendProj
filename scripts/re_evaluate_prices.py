import os
import sys
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel, Field

# Setup environment
# Try to load local .env, but usually production env vars take precedence
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import SessionLocal
import models
from datetime import datetime, timedelta

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("CRITICAL ERROR: No GEMINI_API_KEY found in environment variables.")
    print("Make sure you run this script inside the docker container where the API key is set!")
    sys.exit(1)

genai.configure(api_key=api_key)

class PriceExtraction(BaseModel):
    price: float = Field(description="The extracted real price in JOD. Must be a valid realistic monetary price for the item (e.g. apartment rental, car). If the text mentions random percentages like '99% clean' or durations '1 month', it is NOT a price. If no explicit real price is mentioned, return 0.")

def fix_ads():
    db = SessionLocal()
    # We are looking for ads that we recently forced to 0, OR any scraped ad that currently has price 0.
    # To be safe and target the 178 ads we just zeroed, we can look at ads updated in the last 2 hours
    # that have price = 0 and come from facebook.
    
    time_threshold = datetime.utcnow() - timedelta(hours=2)
    ads = db.query(models.Ad).filter(
        models.Ad.price == 0, 
        models.Ad.source_url.like('%facebook%'),
        models.Ad.updated_at >= time_threshold
    ).all()
    
    print(f"Found {len(ads)} recently zeroed Facebook ads to re-evaluate.")
    if len(ads) == 0:
        print("No ads to process.")
        return
        
    model = genai.GenerativeModel("gemini-2.5-flash")
    system_instruction = (
        "You are a data extraction assistant. Read the following ad description.\n"
        "Extract the REAL monetary price (in JOD) for the item being sold/rented (typically a car, apartment, or land).\n"
        "IMPORTANT: Daily/monthly apartment rentals can legitimately have a price between 1-99 JOD.\n"
        "HOWEVER, if the only numbers you see are small random values (e.g. 'used 1 month', '99% clean', '3 days', '5 years'), then NO real price is mentioned.\n"
        "If no explicit real price is mentioned, return 0."
    )
    
    updated_count = 0
    deleted_count = 0
    
    for idx, ad in enumerate(ads):
        try:
            desc = ad.raw_description or ad.description or ""
            if not desc:
                print(f"[{idx+1}/{len(ads)}] Ad {ad.id} has no description. Deleting...")
                db.delete(ad)
                deleted_count += 1
                continue
                
            prompt = f"Description:\n{desc}"
            
            response = model.generate_content(
                system_instruction + "\n\n" + prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=PriceExtraction,
                    temperature=0.0
                )
            )
            
            res = json.loads(response.text)
            new_price = float(res.get("price", 0))
            
            if new_price > 0:
                print(f"[{idx+1}/{len(ads)}] Updating ad {ad.id} with REAL price: {new_price}")
                ad.price = new_price
                updated_count += 1
            else:
                print(f"[{idx+1}/{len(ads)}] Deleting ad {ad.id} - no valid real price found in text.")
                db.delete(ad)
                deleted_count += 1
                
            time.sleep(0.5) # Prevent rate limits
                
        except Exception as e:
            print(f"[{idx+1}/{len(ads)}] Error processing ad {ad.id}: {e}")
            
    db.commit()
    print(f"\nDone! Updated {updated_count} ads with real prices. Deleted {deleted_count} ads that had no price.")

if __name__ == "__main__":
    fix_ads()

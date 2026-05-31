import os
import time
import googlemaps
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

def main():
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("GOOGLE_API_KEY not found in .env")
        return

    print("Initializing Google Maps API...")
    gmaps = googlemaps.Client(key=api_key)

    db = SessionLocal()
    regions = db.query(models.Region).all()

    updated = 0
    skipped = 0

    print(f"Found {len(regions)} regions to check.")
    for region in regions:
        query = f"{region.name_ar}, {region.city.name_ar}, الأردن"
        try:
            print(f"Geocoding Region ID: {region.id}...")
            geocode_result = gmaps.geocode(query)
            
            if not geocode_result:
                # Try fallback without city
                fallback_query = f"{region.name_ar}, الأردن"
                print(f"  Fallback Geocoding Region ID: {region.id}...")
                geocode_result = gmaps.geocode(fallback_query)

            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                region.latitude = location['lat']
                region.longitude = location['lng']
                print(f"  -> SUCCESS: Lat {region.latitude}, Lng {region.longitude}")
                updated += 1
            else:
                print(f"  -> FAILED to find location.")
            
            # Commit periodically
            if updated % 10 == 0:
                db.commit()

        except Exception as e:
            print(f"  -> ERROR: {e}")

    db.commit()
    print(f"\nFinished. Updated {updated} regions. Skipped {skipped} regions already having coordinates.")

if __name__ == '__main__':
    main()

import os
import time
from geopy.geocoders import Nominatim
from sqlalchemy.orm import Session

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

def main():
    print("Initializing OpenStreetMap Geocoder...")
    geolocator = Nominatim(user_agent="classifieds_app_jordan")

    db = SessionLocal()
    regions = db.query(models.Region).all()

    updated = 0
    skipped = 0

    print(f"Found {len(regions)} regions to check.")
    for region in regions:
        if region.latitude is not None and region.longitude is not None:
            skipped += 1
            continue

        query = f"{region.name_ar}, {region.city.name_ar}, الأردن"
        try:
            print(f"Geocoding Region ID: {region.id}...")
            location = geolocator.geocode(query, timeout=10)
            
            if not location:
                fallback_query = f"{region.name_ar}, الأردن"
                print(f"  Fallback Geocoding Region ID: {region.id}...")
                location = geolocator.geocode(fallback_query, timeout=10)

            if location:
                region.latitude = location.latitude
                region.longitude = location.longitude
                updated += 1
            
            if updated % 5 == 0:
                db.commit()
            
            # Nominatim requires 1 second sleep between requests
            time.sleep(1.1)

        except Exception as e:
            pass

    db.commit()
    print(f"Finished. Updated {updated} regions.")

if __name__ == '__main__':
    main()

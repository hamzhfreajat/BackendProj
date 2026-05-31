import os
import time
from geopy.geocoders import ArcGIS
from sqlalchemy.orm import Session

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

def main():
    print("Initializing ArcGIS Geocoder...")
    geolocator = ArcGIS(user_agent="classifieds_app_jordan")

    db = SessionLocal()
    regions = db.query(models.Region).filter(models.Region.latitude == None).all()

    updated = 0
    skipped = 0

    print(f"Found {len(regions)} regions missing coordinates.")
    for region in regions:
        query_en = f"{region.name_en}, {region.city.name_en}, Jordan" if region.name_en and region.city.name_en else None
        query_ar = f"{region.name_ar}, {region.city.name_ar}, الأردن"
        
        location = None
        try:
            print(f"Geocoding Region ID: {region.id} ({region.name_ar})...")
            
            if query_en:
                location = geolocator.geocode(query_en, timeout=10)
            
            if not location:
                location = geolocator.geocode(query_ar, timeout=10)
                
            if not location and region.name_en:
                fallback_en = f"{region.name_en}, Jordan"
                location = geolocator.geocode(fallback_en, timeout=10)
                
            if not location:
                fallback_ar = f"{region.name_ar}, الأردن"
                location = geolocator.geocode(fallback_ar, timeout=10)

            if location:
                region.latitude = location.latitude
                region.longitude = location.longitude
                updated += 1
                print(f"  -> Found: {location.latitude}, {location.longitude}")
            else:
                print("  -> Not found.")
            
            if updated % 10 == 0:
                db.commit()

        except Exception as e:
            print(f"  -> Error: {e}")

    db.commit()
    print(f"Finished. Updated {updated} regions.")

if __name__ == '__main__':
    main()

import sys
import io
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
from models import City

db = SessionLocal()

cities = db.query(City).all()

dart_code = "  static const Map<String, List<String>> _cityRegions = {\n"

for city in cities:
    if city.regions:
        dart_code += f"    '{city.name_ar}': [\n      "
        
        region_names = sorted([r.name_ar for r in city.regions])
        
        # Format strings properly
        quoted_regions = [f'"{r}"' for r in region_names]
        
        # Join with commas
        regions_str = ", ".join(quoted_regions)
        
        # We also need to keep the "أخرى" region at the end if it's supposed to be there.
        # Looking at the original code, "أخرى" was ALWAYS at the end of every city's list.
        if '"أخرى"' in regions_str:
            regions_str = regions_str.replace(', "أخرى"', '')
            regions_str = regions_str.replace('"أخرى", ', '')
            regions_str += ', "أخرى"'
        else:
            if regions_str:
                regions_str += ', "أخرى"'
            else:
                regions_str = '"أخرى"'
                
        dart_code += regions_str + "\n    ],\n"

dart_code += "  };\n"

with io.open('d:/open/classifieds-app/backend/dart_regions.txt', 'w', encoding='utf-8') as f:
    f.write(dart_code)

print("Generated dart_regions.txt")

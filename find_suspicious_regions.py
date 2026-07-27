import sys, os, re
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session
from collections import defaultdict

db: Session = SessionLocal()
regions = db.query(models.Region).all()

directional_words = ['قرب', 'خلف', 'بجانب', 'مقابل', 'شرق', 'غرب', 'شمال', 'جنوب', 'بين', 'عند', 'منطقة']
landmark_words = ['مستشفى', 'صالة', 'مول', 'دوار', 'شارع', 'مجمع', 'جامعة', 'كازية', 'قهوة', 'منتزه', 'قصر', 'اسكان']

suspicious_directional = []
suspicious_landmarks = []
generic_or_short = []

# For duplicate detection
normalized_map = defaultdict(list)

def normalize_arabic(text):
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ة', 'ه')
    text = text.replace('ّ', '') # remove shaddah
    text = text.replace(' ', '')
    return text

for r in regions:
    name = r.name_ar
    city = db.query(models.City).filter(models.City.id == r.city_id).first()
    city_name = city.name_ar if city else "Unknown"
    
    # 1. Directional
    if any(d in name for d in directional_words):
        suspicious_directional.append((r.id, f"{city_name} - {name}"))
        
    # 2. Landmarks
    elif any(l in name for l in landmark_words):
        suspicious_landmarks.append((r.id, f"{city_name} - {name}"))
        
    # 3. Short / Generic
    elif len(name) <= 3 or name in ['فلل', 'قرية', 'حي', 'ضاحية']:
        generic_or_short.append((r.id, f"{city_name} - {name}"))
        
    # 4. Normalization for duplicates
    # Only consider words with >3 chars to avoid false positives
    if len(name) > 3:
        norm = normalize_arabic(name)
        normalized_map[(city_name, norm)].append((r.id, name))

# Filter normalized map for duplicates (more than 1 entry with same normalized name)
duplicates = []
for (city, norm), items in normalized_map.items():
    if len(items) > 1:
        duplicates.append((city, items))

# Write markdown report
with open('suspicious_regions_report.md', 'w', encoding='utf-8') as f:
    f.write("# Suspicious Regions Report\n\n")
    
    f.write("## 1. Potential Duplicates (Typographical Variations)\n")
    f.write("These regions have almost identical names (differing only by Hamza, Taa Marbuta, or spaces).\n")
    for city, items in duplicates:
        f.write(f"- **City: {city}**\n")
        for id_, name in items:
            f.write(f"  - {name} ({id_})\n")
            
    f.write("\n## 2. Contains Directional or Generic Words\n")
    f.write("These regions contain words like قرب, خلف, شمال, منطقة.\n")
    for id_, name in suspicious_directional:
        f.write(f"- {name} ({id_})\n")
        
    f.write("\n## 3. Contains Landmark Words\n")
    f.write("These regions contain words like دوار, مستشفى, شارع, مول.\n")
    for id_, name in suspicious_landmarks:
        f.write(f"- {name} ({id_})\n")
        
    f.write("\n## 4. Very Short or Generic Names\n")
    for id_, name in generic_or_short:
        f.write(f"- {name} ({id_})\n")

print("Report generated.")

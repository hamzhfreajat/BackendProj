import json
from sqlalchemy.orm import sessionmaker
from models import Ad
from database import SessionLocal

session = SessionLocal()

# 1. Fetch all ads and their IDs
ads = session.query(Ad).filter(Ad.location.like('%أخرى%')).all()

# We need to recreate the same transformation done for single_line
ad_mapping = {}
for ad in ads:
    # Same logic as before if we need to match exactly
    desc = ad.description if ad.description else ""
    single_line_desc = desc.replace('\n', ' ').replace('\r', '')
    line = f"CITY:{ad.location} | AD:{single_line_desc}"
    ad_mapping[line] = ad.id

# 2. Read the chunks and the LLM extracted regions
results = []
missing_matches = 0

with open('all_701_ads_single_line.txt', 'r', encoding='utf-8') as f:
    all_lines = f.read().splitlines()

chunk_files = [f'chunk_{i}_out.json' for i in range(1, 8)]

current_line_idx = 0

for file in chunk_files:
    try:
        with open(file, 'r', encoding='utf-8') as jf:
            chunk_data = json.load(jf)
            
        for item in chunk_data:
            line_text = all_lines[current_line_idx]
            
            # Find ID
            ad_id = ad_mapping.get(line_text)
            if not ad_id:
                # Try finding it without perfect whitespace match or handle uniqueness later
                # For now, print warning
                print(f"Warning: Could not match line {current_line_idx}")
                missing_matches += 1
            else:
                region = item.get('region')
                city = item.get('city') or line_text.split('CITY:')[1].split(',')[0].strip()
                if region and region != 'null':
                    results.append({"id": ad_id, "city": city, "region": region})
            
            current_line_idx += 1
    except FileNotFoundError:
        print(f"{file} not found yet.")

print(f"Total extracted mapping: {len(results)}")
print(f"Total lines matched: {current_line_idx}")
print(f"Missing matches: {missing_matches}")

with open('final_extracted_regions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

session.close()

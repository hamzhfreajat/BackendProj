import os
import json
import psycopg2
from dotenv import load_dotenv
from time import sleep

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("NO API KEY!")
    exit(1)

try:
    from google import genai
    _USE_NEW_SDK = True
except ImportError:
    import google.generativeai as genai
    _USE_NEW_SDK = False

if _USE_NEW_SDK:
    client = genai.Client(api_key=api_key)
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()
cur.execute('''
    SELECT id, location, raw_description 
    FROM ads 
    WHERE location LIKE '%أخرى%' 
''')
ads = cur.fetchall()

print(f"Total ads to process: {len(ads)}")

chunk_size = 20
results = []

prompt_template = """
You are an expert at identifying Jordanian regions from real estate or classified ads.
Given a list of ad descriptions, identify the specific region/neighborhood (المنطقة/الحي) mentioned in the ad.
Important Rules:
1. Ignore anything that contains the word "حوض" (Basin), do not extract it as a region.
2. Return ONLY a valid JSON array of strings in the exact same order as the provided ads. 
3. If an ad doesn't mention a region, return null for that ad.
4. Only extract the specific region name (e.g., "الجبيهة", "الراهبات", "ضاحية الرشيد"), do not include the city name unless it's part of the region name.
5. If the region is written differently, normalize it (e.g. "حي عاليا" -> "حي عالية").

Ads:
{ads_text}

Respond ONLY with a JSON array of strings or nulls, exactly matching the number of ads:
[
  "الجبيهة",
  null,
  "الراهبات"
]
"""

for i in range(0, len(ads), chunk_size):
    chunk = ads[i:i+chunk_size]
    ads_text = "\n".join([f"Ad {idx+1} (City: {loc.split(',')[0]}): {desc}" for idx, (ad_id, loc, desc) in enumerate(chunk)])
    prompt = prompt_template.format(ads_text=ads_text)
    
    try:
        if _USE_NEW_SDK:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = response.text.strip()
        else:
            response = model.generate_content(prompt)
            raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        
        extracted = json.loads(raw.strip())
        for j, reg in enumerate(extracted):
            if j < len(chunk):
                ad_id, loc, desc = chunk[j]
                city = loc.split(',')[0].strip()
                results.append({"id": ad_id, "city": city, "region": reg})
                
        print(f"Processed chunk {i//chunk_size + 1}/{(len(ads)+chunk_size-1)//chunk_size}")
    except Exception as e:
        print(f"Error at chunk {i}: {e}")
        # Add nulls for failed chunk
        for j in range(len(chunk)):
            ad_id, loc, desc = chunk[j]
            city = loc.split(',')[0].strip()
            results.append({"id": ad_id, "city": city, "region": None})
            
    sleep(2)

print(f"Extracted {len([r for r in results if r['region']])} non-null regions.")
with open('ai_extracted_regions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

conn.close()

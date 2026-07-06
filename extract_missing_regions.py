import psycopg2
import re
from collections import Counter
import json

# Load valid regions
city_regions = {}
with open('../all_regions_db.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if '|' in line:
            parts = line.split('|', 1)
            city = parts[0].strip()
            reg = parts[1].strip()
            if city not in city_regions:
                city_regions[city] = []
            city_regions[city].append(reg)

def normalize_arabic(text):
    if not text: return ''
    text = re.sub(r'[أإآا]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ي$', 'ى', text)
    return text

city_regions_norm = {}
for city, regs in city_regions.items():
    city_norm = normalize_arabic(city)
    city_regions_norm[city_norm] = [(r, normalize_arabic(r)) for r in regs]

conn = psycopg2.connect(
    host='178.104.204.148',
    port=9000,
    dbname='cmnynjgg90003aumlerff4j9q',
    user='postgres',
    password='p2j9ggm6cWLAhhVTsbNzYFqK'
)
cur = conn.cursor()

cur.execute('''
    SELECT location, raw_description 
    FROM ads 
    WHERE location LIKE '%أخرى%' 
''')
others_ads = cur.fetchall()
conn.close()

# Location keywords to extract after
# e.g., "في منطقة X", "شارع X", "حي X", "دوار X", "اسكان X", "قرب X"
regex = re.compile(r'(?:في منطقة|في|منطقة|شارع|حي|دوار|اسكان|إسكان|قرب|مقابل|بجانب|خلف|مستشفى|جامعة)\s+([\w\s]{4,30}?)(?=\s+(?:للبيع|للايجار|مساحة|بسعر|قرب|خلف|في|مع|و|\.|،|-|!|\||\n)|$)')

stop_words = {'اربد', 'عمان', 'الزرقاء', 'العقبة', 'المفرق', 'السلط', 'عجلون', 'جرش', 'مادبا', 'الكرك', 'الطفيلة', 'معان', 'فلل', 'شقق', 'شقة', 'اراضي', 'ارض', 'مزرعة', 'مزارع', 'بيت', 'منزل', 'مستقل', 'طابق', 'طوابق', 'ديلوكس', 'سوبر', 'مميز', 'مميزة', 'جميع', 'الخدمات', 'واصل', 'متر', 'مربع', 'دونم', 'غرف', 'نوم', 'حمام', 'مطبخ', 'صالون', 'سعر', 'دينار', 'المالك', 'مباشرة', 'بدون', 'وسيط'}

results = {}

for loc, desc in others_ads:
    if not desc: continue
    city = loc.split(',')[0].strip() if ',' in loc else loc.strip()
    city_norm = normalize_arabic(city)
    desc_norm = normalize_arabic(desc)
    
    # Check if safety net would have caught it
    valid_regs = city_regions_norm.get(city_norm, [])
    caught = any(norm_r in desc_norm for _, norm_r in valid_regs)
    if caught:
        continue # Skip ads that our new safety net already fixes!
        
    # Extract potential locations
    matches = regex.findall(desc)
    for match in matches:
        match = match.strip()
        # Clean up
        words = match.split()
        clean_words = [w for w in words if w not in stop_words and len(w) > 2]
        if not clean_words: continue
        clean_match = ' '.join(clean_words[:3]) # Take max 3 words
        
        if len(clean_match) > 3:
            if city not in results:
                results[city] = Counter()
            results[city][clean_match] += 1

output_lines = ['# Extracted Missing Regions from "Others" Ads\n']
for city, counter in results.items():
    output_lines.append(f'## {city}')
    for reg, count in counter.most_common(10):
        if count >= 2: # Only show if mentioned at least twice
            output_lines.append(f'- {reg} (mentioned {count} times)')
    output_lines.append('')

with open('../missing_regions_extracted.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print('Done')

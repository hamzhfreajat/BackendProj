import psycopg2
import json
import re
from collections import Counter

# 1. Load valid regions per city
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

# Normalize regions for fast scanning
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

# Group ads by city
ads_by_city = {}
for loc, desc in others_ads:
    city = loc.split(',')[0].strip() if ',' in loc else loc.strip()
    city_norm = normalize_arabic(city)
    if city_norm not in ads_by_city:
        ads_by_city[city_norm] = []
    ads_by_city[city_norm].append(desc if desc else '')

def get_ngrams(text, n):
    words = [w for w in re.split(r'\W+', text) if w and len(w) > 2]
    return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

report_lines = ['# Detailed Report on Others (أخرى) Ads by City\n']

for city_norm, descs in ads_by_city.items():
    valid_regs = city_regions_norm.get(city_norm, [])
    
    distraction_count = 0
    missed_regions_found = Counter()
    
    bigrams = Counter()
    trigrams = Counter()
    
    for desc in descs:
        desc_norm = normalize_arabic(desc)
        
        # Check for AI distraction (valid region exists in text)
        found_valid = False
        for orig_r, norm_r in valid_regs:
            if norm_r in desc_norm:
                distraction_count += 1
                missed_regions_found[orig_r] += 1
                found_valid = True
                break # count once per ad
                
        # If no valid region found, it's likely a missing region or no region
        if not found_valid:
            bigrams.update(get_ngrams(desc, 2))
            trigrams.update(get_ngrams(desc, 3))
            
    # Format city report
    city_orig = next((c for c in city_regions.keys() if normalize_arabic(c) == city_norm), city_norm)
    report_lines.append(f'## City: {city_orig} (Total "أخرى": {len(descs)})')
    report_lines.append(f'- **AI Distraction (Region existed in text but AI missed it)**: {distraction_count} ads')
    if missed_regions_found:
        report_lines.append('  - *Top regions the AI missed*: ' + ', '.join(f'{k} ({v})' for k, v in missed_regions_found.most_common(5)))
    
    report_lines.append(f'- **Missing Regions / Unknown**: {len(descs) - distraction_count} ads')
    
    # Filter common phrases
    stops = ['للبيع', 'للايجار', 'من المالك', 'ارضي', 'متر', 'مربع', 'دونم', 'غرف', 'نوم', 'حمام', 'صالون', 'مطبخ', 'مساحة', 'بسعر', 'مغري', 'دينار', 'الف', 'قابل', 'للتفاوض', 'عمان', 'اربد', 'الزرقاء', 'العقبة', 'طابق', 'شقق', 'شقة']
    
    top_bigrams = [f'{k} ({v})' for k, v in bigrams.most_common(30) if v > 2 and not any(s in k for s in stops)][:5]
    top_trigrams = [f'{k} ({v})' for k, v in trigrams.most_common(30) if v > 2 and not any(s in k for s in stops)][:5]
    
    if top_bigrams or top_trigrams:
        report_lines.append('  - *Potential Missing Regions (Common Phrases)*:')
        if top_trigrams:
            report_lines.append('    - ' + ', '.join(top_trigrams))
        if top_bigrams:
            report_lines.append('    - ' + ', '.join(top_bigrams))
            
    report_lines.append('\n')

with open('../others_detailed_report.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print('Report generated')

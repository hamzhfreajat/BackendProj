import json
import sys
import re

def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[\u064B-\u0652]', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    with open('valid_locations.json', 'r', encoding='utf-8') as f:
        valid_locations = json.load(f)

    with open('others_chunk_10.json', 'r', encoding='utf-8') as f:
        ads = json.load(f)

    print(f"Total ads to process: {len(ads)}")

    # We will generate inspectable chunks of ads
    for batch_start in range(0, len(ads), 30):
        batch_end = min(batch_start + 30, len(ads))
        print(f"\n==================== BATCH {batch_start} to {batch_end-1} ====================")
        for i in range(batch_start, batch_end):
            ad = ads[i]
            print(f"[{i}] ID: {ad.get('id')}")
            print(f"  Title: {ad.get('title')}")
            desc_snippet = ad.get('desc', '').replace('\n', ' ')
            if len(desc_snippet) > 200:
                desc_snippet = desc_snippet[:200] + "..."
            print(f"  Desc:  {desc_snippet}")
            print("-" * 50)

if __name__ == '__main__':
    main()

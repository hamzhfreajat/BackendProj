import json
import sys
import re

def normalize_arabic(text):
    if not text:
        return ""
    text = re.sub(r'[أإآٱ]', 'ا', text)
    text = re.sub(r'ة', 'ه', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'[\u064B-\u0652]', '', text) # remove tashkeel
    text = re.sub(r'[^\w\s,]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    with open('valid_locations.json', 'r', encoding='utf-8') as f:
        valid_locations = json.load(f)
    
    with open('others_chunk_10.json', 'r', encoding='utf-8') as f:
        ads = json.load(f)

    with open('chunk10_review.txt', 'w', encoding='utf-8') as out:
        out.write(f"Total valid locations: {len(valid_locations)}\n")
        out.write(f"Total ads: {len(ads)}\n\n")

        for idx, ad in enumerate(ads):
            ad_id = str(ad.get("id"))
            title = ad.get("title", "")
            desc = ad.get("desc", "")
            
            out.write(f"=== INDEX {idx} | ID {ad_id} ===\n")
            out.write(f"TITLE: {title}\n")
            out.write(f"DESC: {desc}\n")
            out.write("-" * 40 + "\n")

    print(f"Dumped {len(ads)} ads to chunk10_review.txt")

if __name__ == '__main__':
    main()

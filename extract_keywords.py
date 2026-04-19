import os
import sys
import string
import json
from collections import Counter
from database import SessionLocal
import models
import re

def main():
    db = SessionLocal()
    try:
        c_all = db.query(models.Category).all()
        re_ids = set()
        for c in c_all:
            if any(k in c.name for k in ["عقار", "شقق", "شقة", "سكن", "فيلات", "اراضي", "أراضي", "شاليه", "مزرعة", "عمارة", "مكتب", "تجاري"]):
                re_ids.add(c.id)
                for child in c_all:
                    if child.parent_id == c.id:
                        re_ids.add(child.id)
        
        ads = db.query(models.Ad.description).filter(models.Ad.category_id.in_(re_ids)).all()
        text_corpus = " ".join([ad[0] for ad in ads if ad[0]])
        words = re.findall(r'[\u0600-\u06FF]+', text_corpus)
        
        stop_words = set(["في", "من", "على", "الى", "إلى", "عن", "مع", "و", "أو", "لا", "ما", "لم", "لن", "هل", "قد", "لقد", "كان", "كانت", "يكون", "الله", "بسم", "السلام", "عليكم", "للبيع", "للايجار", "رقم", "التواصل", "الرجاء"])
        filtered_words = [w for w in words if len(w) >= 3 and w not in stop_words]
        
        counter = Counter(filtered_words)
        output = [word for word, count in counter.most_common(80) if count > 5]
        
        with open('keywords_output.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
    finally:
        db.close()

if __name__ == '__main__':
    main()

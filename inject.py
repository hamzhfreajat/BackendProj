import sys
sys.path.append('d:\\open\\classifieds-app\\backend')

with open('d:\\open\\classifieds-app\\backend\\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

func_def = '''
def parse_smart_search_query(q: str, db):
    from main import norm_str, expand_term_with_synonyms, SEARCH_SYNONYMS, norm_col
    import models
    norm_q = norm_str(q)
    inferred_cat_id = None
    inferred_cat_name = None
    inferred_loc = None
    inferred_tags = []
    
    raw_search_terms = set(norm_q.split())
    search_terms = set()
    for t in raw_search_terms:
        search_terms.add(t)
        search_terms.update(expand_term_with_synonyms(t))
        if t == 'استوديوهات': search_terms.add('ستوديوهات')
        if t == 'ستوديوهات': search_terms.add('استوديوهات')
    
    remaining_terms = set(norm_q.split())
    expanded_remaining = set(remaining_terms)
    for term in remaining_terms:
        expanded_remaining.update(expand_term_with_synonyms(term))
    
    all_cats = db.query(models.Category).all()
    cat_matches = []
    for cat in all_cats:
        cat_norm = norm_str(cat.name)
        cat_terms = set(cat_norm.split())
        if cat_terms and cat_terms.issubset(expanded_remaining):
            priority = 1 if cat_norm in norm_q else 0
            cat_matches.append((cat.id, len(cat_terms), cat.name, priority, cat_terms))
            
    if cat_matches:
        cat_matches.sort(key=lambda x: (x[3], x[1], x[0]), reverse=True)
        inferred_cat_id = cat_matches[0][0]
        inferred_cat_name = cat_matches[0][2]
        
        words_to_remove = set()
        for w in remaining_terms:
            w_syns = expand_term_with_synonyms(w)
            if any(syn in cat_matches[0][4] for syn in [w] + w_syns):
                words_to_remove.add(w)
        remaining_terms -= words_to_remove
    else:
        for k, synonyms in SEARCH_SYNONYMS.items():
            for syn in synonyms:
                if syn in remaining_terms:
                    from sqlalchemy import func
                    synonym_match = db.query(models.Category).filter(models.Category.name.ilike(f"%{k}%")).order_by(func.length(models.Category.name)).first()
                    if synonym_match:
                        inferred_cat_id = synonym_match.id
                        inferred_cat_name = synonym_match.name
                        remaining_terms.discard(syn)
                        break
            if inferred_cat_id:
                break
        
    import re
    price_match = re.search(r'(?:بسعر|سعر|لا يتجاوز|اقل من|بحدود)\s*(\d+)\s*(ألف|الف|000)?(?!\s*متر|\s*م\b|\s*m\b)', q)
    if not price_match:
        price_match = re.search(r'(\d+)\s*(ألف|الف)(?!\s*متر|\s*م\b|\s*m\b)', q)
    if price_match:
        base_price = int(price_match.group(1))
        if price_match.lastgroup and price_match.group(price_match.lastindex) in ["ألف", "الف"]:
            base_price *= 1000
        elif price_match.group(0).endswith("ألف") or price_match.group(0).endswith("الف"):
             base_price *= 1000
        inferred_tags.append(f"max_price:{base_price}")
        for word in price_match.group(0).split():
            remaining_terms.discard(word)
            
    area_match = re.search(r'(?:مساحة|مساحتها|بمساحة)?\s*(\d+)\s*(?:متر|م\b|m\b)', q)
    if area_match:
        remaining_terms.add(area_match.group(1))
        for word in area_match.group(0).split():
            if word != area_match.group(1):
                remaining_terms.discard(word)
                
    bed_match = re.search(r'(\d+)\s*(?:نوم|غرف)', q)
    if bed_match:
        inferred_tags.append(f"bedrooms:{bed_match.group(1)}")
        for w in bed_match.group(0).split():
            remaining_terms.discard(w)
    elif "غرفتين" in remaining_terms:
        inferred_tags.append("bedrooms:2")
        remaining_terms.discard("غرفتين")
        if "وصاله" in remaining_terms: remaining_terms.discard("وصاله")
        if "وصالة" in remaining_terms: remaining_terms.discard("وصالة")
    
    noise_words = {"في", "مع", "من", "او", "لا", "الى", "لل", "على", "عن", "ب", "ل", "و", "ف", "ك"}
    remaining_terms -= noise_words
    
    import main
    if main.LOCATIONS_CACHE is None:
        cities = [c[0] for c in db.query(models.City.name_ar).all()]
        regions = [r[0] for r in db.query(models.Region.name_ar).all()]
        locs = list(set(cities + regions))
        locs.sort(key=len, reverse=True)
        main.LOCATIONS_CACHE = locs
        
    for loc in main.LOCATIONS_CACHE:
        loc_words = norm_str(loc).split()
        matched_words = set()
        match = True
        for lw in loc_words:
            found_term = None
            for term in remaining_terms:
                if term == lw:
                    found_term = term
                    break
                if term.endswith(lw) and len(term) <= len(lw) + 2 and term[:-len(lw)] in ['ب', 'ل', 'و', 'ف', 'كال']:
                    found_term = term
                    break
                if lw.startswith('ال') and term == f"لل{lw[2:]}":
                    found_term = term
                    break
            if found_term:
                matched_words.add(found_term)
            else:
                match = False
                break
        
        if match:
            inferred_loc = loc
            remaining_terms -= matched_words
            break
            
    multi_quick_tags = {
        "غير مفروشه": "furnished:غير مفروشة", 
        "طابق ارضي": "floor:الطابق الأرضي",
        "شبه ارضي": "floor:طابق شبه أرضي",
        "طابق اول": "floor:1",
        "طابق ثاني": "floor:2",
        "طابق ثالث": "floor:3",
        "طابق رابع": "floor:4",
        "طابق خامس": "floor:5",
        "طابق اخير": "floor:الطابق الأخير",
        "تحت الانشاء": "building_age:تحت الإنشاء",
        "ايجار يومي": "rent_duration:يومي",
        "ايجار شهري": "rent_duration:شهري",
        "ايجار سنوي": "rent_duration:سنوي",
        "للايجار اليومي": "rent_duration:يومي",
        "للايجار الشهري": "rent_duration:شهري",
        "للايجار السنوي": "rent_duration:سنوي",
        "بدون عموله": "seller_type:المالك",
        "بدون وسيط": "seller_type:المالك",
        "طاقه شمسيه": "main_features:طاقة شمسية",
        "تدفئه مركزيه": "main_features:تدفئة",
        "تحت البلاط": "main_features:تدفئة",
        "بئر ماء": "main_features:بئر ماء",
        "مطبخ راكب": "main_features:مطبخ راكب",
        "غير مفروش": "furnished:غير مفروشة"
    }
    for k, v in multi_quick_tags.items():
        tag_words = set(k.split())
        if tag_words.issubset(remaining_terms):
            inferred_tags.append(v)
            remaining_terms -= tag_words
                
    single_quick_tags = {
        "مفروشه": "furnished:مفروشة",
        "مفروش": "furnished:مفروشة",
        "بالتقسيط": "installment_possible:نعم",
        "تقسيط": "installment_possible:نعم",
        "جديده": "building_age:جديد لم يسكن",
        "ارضيه": "floor:الطابق الأرضي",
        "مسبح": "main_features:مسبح",
        "ومسبح": "main_features:مسبح",
        "تكييف": "main_features:تكييف",
        "مصعد": "main_features:مصعد",
        "كراج": "main_features:كراج",
        "انترنت": "main_features:إنترنت",
        "استوديو": "bedrooms:0",
        "استوديوهات": "bedrooms:0"
    }
    for k, v in single_quick_tags.items():
        if k in remaining_terms:
            inferred_tags.append(v)
            remaining_terms.discard(k)
            
    remaining_search = " ".join(remaining_terms) if remaining_terms else None
    
    return inferred_cat_id, inferred_cat_name, inferred_loc, inferred_tags, remaining_search

'''

import re
new_content = re.sub(
    r'@app\.get\("/api/search/autocomplete"\)',
    func_def + r'\n@app.get("/api/search/autocomplete")',
    content
)

autocomplete_new = '''    if len(q) >= 3:
        inferred_cat_id, inferred_cat_name, inferred_loc, inferred_tags, remaining_search = parse_smart_search_query(q, db)'''

new_content = re.sub(r'    if len\(q\) >= 3:.*?remaining_search = " ".join\(remaining_terms\) if remaining_terms else None', autocomplete_new, new_content, flags=re.DOTALL)

with open('d:\\open\\classifieds-app\\backend\\main.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print('Replaced search_autocomplete block.')

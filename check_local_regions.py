import json

try:
    with open('final_extracted_regions.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    names = set()
    for r in data:
        n = r.get('name_ar', '').strip()
        if n: names.add(n)
        for alias in r.get('aliases', []):
            if alias.strip():
                names.add(alias.strip())
            
    check = [
        'دوار الداخلية', 'جبيهة', 'المدينة الرياضية', 'دوار الواحة', 
        'ابو نصير', 'ام زويتيه', 'ضاحية الرشيد', 'ام السماق', 'شارع المدينة المنورة'
    ]
    
    with open('check_results.txt', 'w', encoding='utf-8') as out:
        for c in check:
            found = False
            for n in names:
                if c in n or n in c:
                    out.write(f'FOUND: {c} (matched {n})\n')
                    found = True
                    break
            if not found:
                out.write(f'MISSING: {c}\n')
except Exception as e:
    with open('check_results.txt', 'w', encoding='utf-8') as out:
        out.write(str(e))

import json
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    with open('valid_locations.json', 'r', encoding='utf-8') as f:
        valid_locations = set(json.load(f))

    with open('others_chunk_10.json', 'r', encoding='utf-8') as f:
        ads = json.load(f)

    # Dictionary containing mapped status and location for each ad
    mapping = {
        "26981": {"status": "missing", "location": "إربد, خلف سمايل"},
        "26980": {"status": "missing", "location": "إربد, بني كنانة"},
        "26987": {"status": "missing", "location": "إربد, مجمع عمان الجديد"},
        "26993": {"status": "mapped", "location": "إربد, شارع الحصن"},
        "27003": {"status": "missing", "location": "مادبا, كفير أبو خينان"},
        "27006": {"status": "missing", "location": "إربد, شارع الجامعة"},
        "27004": {"status": "mapped", "location": "إربد, دوار العيادات"},
        "27007": {"status": "mapped", "location": "إربد, مجمع الأغوار الجديد"},
        "27009": {"status": "mapped", "location": "إربد, الحي الشرقي"},
        "27010": {"status": "missing", "location": "جرش, مزرعة الشواهد"},
        "27016": {"status": "mapped", "location": "عمان, ام السماق"},
        "25912": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "27028": {"status": "missing", "location": "إربد, شارع السينما"},
        "27033": {"status": "mapped", "location": "إربد, لواء الطيبة"},
        "25916": {"status": "mapped", "location": "عمان, ضاحية الرشيد"},
        "25163": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "27037": {"status": "mapped", "location": "عمان, طريق المطار"},
        "25471": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "27047": {"status": "missing", "location": "عمان, إسكان المالية والزراعة"},
        "27049": {"status": "mapped", "location": "عمان, ام السماق"},
        "27051": {"status": "missing", "location": "جرش, تلعة الرز"},
        "24686": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "24623": {"status": "mapped", "location": "عمان, الجبيهة"},
        "27663": {"status": "mapped", "location": "عمان, السرو"},
        "27669": {"status": "none", "location": None},
        "27091": {"status": "mapped", "location": "الزرقاء, صروت"},
        "27092": {"status": "mapped", "location": "المفرق, ارحاب"},
        "27095": {"status": "mapped", "location": "عمان, ابو نصير"},
        "27692": {"status": "mapped", "location": "عمان, ضاحية الأمير علي"},
        "27102": {"status": "mapped", "location": "مادبا, دليله الحمايده"},
        "27706": {"status": "missing", "location": "المفرق, البستانة"},
        "27711": {"status": "missing", "location": "عمان, شارع الإذاعة والتلفزيون"},
        "27712": {"status": "mapped", "location": "عمان, أخرى"},
        "27124": {"status": "mapped", "location": "الزرقاء, جريبا"},
        "27729": {"status": "missing", "location": "إربد, شارع السرور"},
        "27733": {"status": "missing", "location": "إربد, قصر العوادين"},
        "27734": {"status": "missing", "location": "إربد, سوق الحدادين"},
        "27133": {"status": "mapped", "location": "عمان, ابو نصير"},
        "27741": {"status": "mapped", "location": "عمان, ابو نصير"},
        "27149": {"status": "mapped", "location": "عمان, طبربور"},
        "27150": {"status": "mapped", "location": "عمان, ام نوارة"},
        "27744": {"status": "mapped", "location": "عمان, ضاحية الأمير علي"},
        "27159": {"status": "missing", "location": "السلط, وادي الناقة"},
        "27160": {"status": "mapped", "location": "عمان, ابو علندا"},
        "27747": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "27756": {"status": "mapped", "location": "عمان, ام اذينة"},
        "27170": {"status": "mapped", "location": "عمان, سالم"},
        "27172": {"status": "mapped", "location": "عمان, بيرين"},
        "27188": {"status": "mapped", "location": "عمان, ابو نصير"},
        "27197": {"status": "mapped", "location": "إربد, دوار اللوازم"},
        "27203": {"status": "missing", "location": "مادبا, العريش"},
        "27205": {"status": "mapped", "location": "السلط, عين الباشا"},
        "27220": {"status": "missing", "location": "عمان, أبو علياء"},
        "27219": {"status": "missing", "location": "عمان, ضاحية الأميرة سلمى"},
        "27809": {"status": "mapped", "location": "عمان, ابو علندا"},
        "27228": {"status": "missing", "location": "إربد, ضاحية الحسين"},
        "27815": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "27829": {"status": "missing", "location": "العقبة, الجمعية"},
        "25883": {"status": "mapped", "location": "عمان, ضاحية الرشيد"},
        "26648": {"status": "mapped", "location": "عمان, جبل الزهور"},
        "25885": {"status": "mapped", "location": "عمان, ابو علندا"},
        "27259": {"status": "missing", "location": "إربد, مجمع عمان الجديد"},
        "27855": {"status": "mapped", "location": "العقبة, السكنية 10"},
        "27857": {"status": "missing", "location": "العقبة, المنطقة السابعة"},
        "27858": {"status": "missing", "location": "العقبة, السكنية 8"},
        "27350": {"status": "missing", "location": "عمان, إسكان المالية والزراعة"},
        "27875": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27865": {"status": "mapped", "location": "العقبة, المحدود الشرقي"},
        "27866": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27868": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27869": {"status": "missing", "location": "العقبة, المنطقة السابعة"},
        "27872": {"status": "mapped", "location": "العقبة, المحدود الوسط"},
        "27873": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27876": {"status": "missing", "location": "العقبة, السكنية 8"},
        "27879": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27880": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27881": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27882": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "24560": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "25099": {"status": "mapped", "location": "الطفيلة, العيص"},
        "25319": {"status": "mapped", "location": "الكرك, الثنية"},
        "25323": {"status": "mapped", "location": "الكرك, الثنية"},
        "25598": {"status": "missing", "location": "جرش, عين التنور"},
        "25779": {"status": "missing", "location": "إربد, دار العلوم"},
        "26064": {"status": "missing", "location": "إربد, دار العلوم"},
        "26112": {"status": "missing", "location": "إربد, دار العلوم"},
        "26754": {"status": "mapped", "location": "السلط, الخضر"},
        "26673": {"status": "missing", "location": "المفرق, الحي الجنوبي"},
        "27826": {"status": "mapped", "location": "العقبة, أخرى"},
        "27828": {"status": "missing", "location": "العقبة, المحدود الغربي"},
        "27884": {"status": "missing", "location": "العقبة, السكنية 9"},
        "27306": {"status": "mapped", "location": "عمان, ضاحية الأمير علي"},
        "27892": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27893": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27896": {"status": "mapped", "location": "الزرقاء, حي معصوم"},
        "27898": {"status": "mapped", "location": "عمان, خلدا"},
        "27899": {"status": "mapped", "location": "عمان, ابو نصير"},
        "27901": {"status": "missing", "location": "العقبة, السكنية 9"},
        "27902": {"status": "missing", "location": "العقبة, المنطقة السابعة"},
        "27903": {"status": "missing", "location": "العقبة, السكنية 9"},
        "27905": {"status": "missing", "location": "العقبة, السكنية 6"},
        "27906": {"status": "missing", "location": "العقبة, المنطقة الخامسة"},
        "27907": {"status": "missing", "location": "العقبة, السكنية 9"},
        "27909": {"status": "mapped", "location": "العقبة, المحدود الوسط"},
        "27911": {"status": "missing", "location": "العقبة, السكنية 11"},
        "27912": {"status": "missing", "location": "العقبة, السكنية 9"},
        "27374": {"status": "mapped", "location": "عمان, شارع الجامعة"},
        "26517": {"status": "mapped", "location": "عمان, ضاحية الاستقلال"},
        "27915": {"status": "mapped", "location": "عمان, طريق المطار"},
        "27921": {"status": "mapped", "location": "إربد, مستشفى الأميرة بسمة"},
        "27923": {"status": "mapped", "location": "الزرقاء, صروت"},
        "27935": {"status": "missing", "location": "مادبا, حوض سمكة"},
        "27936": {"status": "mapped", "location": "مادبا, دليله الحمايده"},
        "27937": {"status": "mapped", "location": "مادبا, حنينا الغربيه"},
        "27939": {"status": "missing", "location": "الزرقاء, دوار أبو سبيتان"},
        "27943": {"status": "missing", "location": "إربد, حريثين"}
    }

    # Verification: Check total ad count
    print(f"Total ads in chunk: {len(ads)}")
    print(f"Total mapped keys: {len(mapping)}")

    ad_ids_in_chunk = set(str(ad['id']) for ad in ads)
    missing_keys = ad_ids_in_chunk - set(mapping.keys())
    extra_keys = set(mapping.keys()) - ad_ids_in_chunk

    if missing_keys:
        print(f"ERROR: Missing keys: {missing_keys}")
    if extra_keys:
        print(f"ERROR: Extra keys: {extra_keys}")

    # Validate each entry against valid_locations rules
    mapped_count = 0
    missing_count = 0
    none_count = 0

    for k, v in mapping.items():
        st = v["status"]
        loc = v["location"]
        if st == "mapped":
            mapped_count += 1
            if loc not in valid_locations:
                print(f"INVALID MAPPED LOCATION for ID {k}: '{loc}' is not in valid_locations.json!")
        elif st == "missing":
            missing_count += 1
            if loc is None:
                print(f"INVALID MISSING entry for ID {k}: location is None!")
        elif st == "none":
            none_count += 1
            if loc is not None:
                print(f"INVALID NONE entry for ID {k}: location should be None but got '{loc}'!")

    print(f"Validation complete! Mapped: {mapped_count}, Missing: {missing_count}, None: {none_count}")

    # Write output to ai_mapped_10.json
    with open('ai_mapped_10.json', 'w', encoding='utf-8') as out:
        json.dump(mapping, out, ensure_ascii=False, indent=2)

    print("Successfully written result to d:/open/classifieds-app/backend/ai_mapped_10.json")

if __name__ == '__main__':
    main()

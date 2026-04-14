import json

with open('brands.json', 'r', encoding='utf-8') as f:
    brands_data = json.load(f)

if 'result' in brands_data and 'data' in brands_data['result']:
    data = brands_data['result']['data']
    if 'options' in data:
        print("BRAND OPTIONS (first 3):")
        for opt in data['options'][:3]:
            print(opt)
    else:
        print("Brands data keys:", data.keys())
else:
    print("Brands raw keys:", brands_data.keys())
    if 'result' in brands_data:
        print("Result keys:", brands_data['result'].keys())

with open('sub_brands.json', 'r', encoding='utf-8') as f:
    sub_brands_data = json.load(f)

if 'result' in sub_brands_data and 'data' in sub_brands_data['result']:
    data = sub_brands_data['result']['data']
    if 'options' in data:
        print("\nSUB BRAND OPTIONS (first 3):")
        for opt in data['options'][:3]:
            print(opt)
    else:
        print("\nSubBrands data keys:", data.keys())
else:
    print("\nSubBrands raw keys:", sub_brands_data.keys())
    if 'result' in sub_brands_data:
        print("SubBrands Result keys:", sub_brands_data['result'].keys())

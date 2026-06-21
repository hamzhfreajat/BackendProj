import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    if only_others:
        query = query.filter(or_(
            models.Ad.location.ilike("%????%"),
            models.Ad.location.ilike("%????%"),
            models.Ad.location.ilike("%other%")
        ))'''

replacement = '''    if only_others:
        query = query.filter(or_(
            models.Ad.location.ilike("%أخرى%"),
            models.Ad.location.ilike("%اخرى%"),
            models.Ad.location.ilike("%other%")
        ))'''

if target in content:
    new_content = content.replace(target, replacement)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS")
else:
    print("TARGET NOT FOUND")

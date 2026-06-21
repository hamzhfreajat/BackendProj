import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'if only_others:\s*query = query\.filter\(or_\(\s*models\.Ad\.location\.ilike\("[^"]*"\),\s*models\.Ad\.location\.ilike\("[^"]*"\),\s*models\.Ad\.location\.ilike\("%other%"\)\s*\)\)'

replacement = '''if only_others:
        query = query.filter(or_(
            models.Ad.location.ilike("%أخرى%"),
            models.Ad.location.ilike("%اخرى%"),
            models.Ad.location.ilike("%other%")
        ))'''

if re.search(pattern, content):
    new_content = re.sub(pattern, replacement, content)
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS")
else:
    print("TARGET NOT FOUND")

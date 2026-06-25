import re

with open(r'd:\open\classifieds-app\backend\seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove line containing 18025
content = re.sub(r'[ \t]*\(18025,[^\n]+\n', '', content)

with open(r'd:\open\classifieds-app\backend\seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed 18025 from seed_categories.py")

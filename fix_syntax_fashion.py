import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The offending floating string:
target = '    {"ar": ["ماركات", "تصفية", "ستوكات", "توصيل مجاني"], "en": ["Brands", "Clearance", "Stock", "Free Delivery"]}),\n'
content = content.replace(target, '')

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Syntax error patched")

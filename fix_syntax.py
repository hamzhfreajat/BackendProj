import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The offending floating string:
target = '    {"ar": ["بسكليت", "فيب", "أراجيل", "أثقال", "تخييم"], "en": ["Bicycle", "Vape", "Hookah", "Weights", "Camping"]}),\n'
content = content.replace(target, '')

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Syntax error patched")

import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The offending floating string:
target = '    {"ar": ["نقل عفش", "صيانة عامة", "مواسرجي", "كهربجي"], "en": ["Moving", "Maintenance", "Plumber", "Electrician"]}),\n'
content = content.replace(target, '')

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Syntax error patched")

import re

with open(r'd:\open\classifieds-app\backend\extraction_constants.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove line starting with ID: 18025
content = re.sub(r'ID: 18025 \| [^\n]+\n', '', content)

with open(r'd:\open\classifieds-app\backend\extraction_constants.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Removed 18025 from extraction_constants.py")

import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace exact strings for Category 7
content = content.replace(
    '(7,  None, "أثاث وديكور", "غرف نوم، صالونات، أدوات مطبخ، ومفروشات", "chair", "#795548", None, {"en": ["Furniture & Decor"]}),',
    '(7,  None, "المنزل", "غرف نوم، صالونات، أدوات مطبخ، ومفروشات", "chair", "#795548", None, {"en": ["Home"]}),'
)

# Replace the generated tree comment string
content = content.replace(
    '# HOME AND GARDEN (parent=7)',
    '# HOME (parent=7)'
)
content = content.replace(
    '(7, None, "المنزل والحديقة", "أثاث، ديكور، حدائق، وأدوات منزلية", "chair", "#795548", None, {"en": ["Home & Garden"]}),',
    '(7, None, "المنزل", "أثاث، ديكور، حدائق، وأدوات منزلية", "chair", "#795548", None, {"en": ["Home"]}),'
)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("seed_categories.py updated successfully!")

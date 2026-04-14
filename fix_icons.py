import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Swap smartphone and هواتف ...
text = re.sub(r'"smartphone",\s*"هواتف(.*?)"', r'"هواتف\1", "smartphone"', text)

# Swap devices_other and موبايل ...
text = re.sub(r'"devices_other",\s*"موبايل(.*?)"', r'"موبايل\1", "devices_other"', text)

with open('seed_categories.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed icon and description swap!")

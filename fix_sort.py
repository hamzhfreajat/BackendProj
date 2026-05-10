import os
import re

filepath = r'd:\open\classifieds-app\frontend\lib\screens\add_ad_subcategories.dart'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_order = '''final order = {
               'محلات': 0,
               'مكاتب': 1,
               'معارض تجارية': 2,
               'صالونات': 3,
               'مطاعم': 4,
               'مخازن': 5,
               'عيادات': 6,
               'مراكز': 7,
               'صالات': 8,
               'فنادق': 9,
               'أراضي': 10,
               'مباني': 11,
             };'''

# Replace the specific order array
# Look for 'final order = {' inside the 'تجاري' block
pattern = r"final order = \{.*?\};"

def replacer(match):
    # Only replace if it contains 'مكاتب': 0
    if "'مكاتب': 0" in match.group(0):
        return new_order
    return match.group(0)

new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
    
print('Updated add_ad_subcategories.dart')

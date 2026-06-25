import re

with open(r'd:\open\classifieds-app\backend\fb_batch_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_rules = """    5. NEVER output relative descriptions like 'قرب', 'خلف', 'بجانب', 'شرق', 'جنوب', 'مقابل'. You MUST extract ONLY the exact official name of the neighborhood/region from the Valid Regions List.
    6. 'البارحة', 'مستشفى بديعة', 'دوار صحارى', 'دوار العيادات', 'دوار الثقافة', 'دوار النسيم', 'مجمع عمان', 'شارع فلسطين' are ALL strictly in 'إربد' (Irbid), NOT Amman! If you see them, format as 'إربد, البارحة' etc."""

# Find the location rules block and append the new rules to the end of each
# The easiest way is to find rule 4 and append 5 and 6 after it.

pattern = re.compile(r'(If an ad mentions being near or at a specific university[^\n]+)')

def replacer(match):
    return match.group(1) + "\n" + new_rules

new_content = pattern.sub(replacer, content)

with open(r'd:\open\classifieds-app\backend\fb_batch_router.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated fb_batch_router.py")

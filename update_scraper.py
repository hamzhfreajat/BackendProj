import re

with open(r'd:\open\classifieds-app\backend\scraper.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_rules = """6. CRITICAL LOCATION RULES: Be very precise with locations. 'العاشرة' typically means 'العقبة, المنطقة العاشرة' NOT 'عمان, الدوار العاشر'. Do not confuse 'بدر' with 'بدر الجديدة'.
7. NEVER output relative descriptions like 'قرب', 'خلف', 'بجانب', 'شرق', 'جنوب', 'مقابل'. You MUST extract ONLY the exact official name of the neighborhood/region.
8. 'البارحة', 'مستشفى بديعة', 'دوار صحارى', 'دوار العيادات', 'دوار الثقافة', 'دوار النسيم', 'مجمع عمان', 'شارع فلسطين' are ALL strictly in 'إربد' (Irbid), NOT Amman! If you see them, format as 'إربد, البارحة' etc. Do not hallucinate cities."""

pattern = re.compile(r'"6\. CRITICAL LOCATION RULES:[^"]+"')

def replacer(match):
    # Python source code formatting for string literal
    escaped_rules = new_rules.replace('\n', '\\n')
    return f'"{escaped_rules}"'

new_content = pattern.sub(replacer, content)

with open(r'd:\open\classifieds-app\backend\scraper.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated scraper.py")

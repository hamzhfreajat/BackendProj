import re

with open(r'd:\open\classifieds-app\backend\fb_batch_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = "If you cannot determine the exact region from the text, return the closest matching valid region based on the city. If a landmark, hospital, roundabout, or street is mentioned, use your geographic knowledge of Jordan to determine its city and closest region. NEVER keep it as is if it contains relative words like 'قرب', 'خلف', 'مقابل' or if it's not in the Valid Regions List. You MUST output either a region from the Valid Regions List, OR just the City name if completely unknown."

# Fallback string since the previous replace might have been slightly different
old_str_2 = "If you cannot determine the exact region from the text, return the closest matching valid region based on the city, If a landmark, hospital, roundabout, or street is mentioned, use your geographic knowledge of Jordan to determine its city and closest region. NEVER keep it as is if it contains relative words like 'قرب', 'خلف', 'مقابل' or if it's not in the Valid Regions List. You MUST output either a region from the Valid Regions List, OR just the City name if completely unknown."

new_str = "If you cannot determine the exact region from the text, use your geographic knowledge of Jordan to determine its correct city and region. If the exact neighborhood is NOT in the Valid Regions List, you MAY create a new region name, BUT it MUST be the official real name of the neighborhood/landmark and MUST be placed in the CORRECT city (e.g. 'إربد, دوار العيادات'). NEVER output relative descriptions or directions like 'قرب', 'خلف', 'بجانب', 'شرق', 'جنوب', 'مقابل' (e.g. 'شرق جرش' or 'قرب دوار الطيارة' is STRICTLY FORBIDDEN, you must strip these words and just output the core region). If you are completely unsure, output the City name only."

content = content.replace(old_str, new_str)
content = content.replace(old_str_2, new_str)

with open(r'd:\open\classifieds-app\backend\fb_batch_router.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated fb_batch_router.py to allow smart new regions")

import re

with open(r'd:\open\classifieds-app\backend\fb_batch_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_str = "or keep it as is if completely unknown, but try your best to find a valid region from the list."
new_str = "If a landmark, hospital, roundabout, or street is mentioned, use your geographic knowledge of Jordan to determine its city and closest region. NEVER keep it as is if it contains relative words like 'قرب', 'خلف', 'مقابل' or if it's not in the Valid Regions List. You MUST output either a region from the Valid Regions List, OR just the City name if completely unknown."

content = content.replace(old_str, new_str)

with open(r'd:\open\classifieds-app\backend\fb_batch_router.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated fb_batch_router.py with smart logic")

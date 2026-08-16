import os

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if location and len(location) > 10:',
    'if location and len(location) > 100:'
)
content = content.replace(
    'Maximum 10 locations allowed per search.',
    'Maximum 100 locations allowed per search.'
)
content = content.replace(
    'if tags and len(tags) > 15:',
    'if tags and len(tags) > 100:'
)
content = content.replace(
    'Maximum 15 tags allowed per search.',
    'Maximum 100 tags allowed per search.'
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Limits updated.")

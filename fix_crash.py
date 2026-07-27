import sys

filepath = 'fb_batch_router.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the template string
content = content.replace('{get_dynamic_location_rules()}', '{dynamic_location_rules}')

# Remove the hacky replace lines
lines = content.split('\n')
new_lines = []
skip = False
for line in lines:
    if "if '{dynamic_location_rules}' in _GEMINI_BATCH_PROMPT:" in line or "if '{get_dynamic_location_rules()}' in _GEMINI_BATCH_PROMPT:" in line:
        skip = True
    elif "if '{dynamic_location_rules}' in _GEMMA_SINGLE_PROMPT:" in line or "if '{get_dynamic_location_rules()}' in _GEMMA_SINGLE_PROMPT:" in line:
        skip = True
        
    if skip and "get_dynamic_location_rules()" in line and "replace" in line:
        continue # skip the replace line
    elif skip and line.strip() == "":
        skip = False # stop skipping after empty line
        continue
    elif skip:
        continue
        
    new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("Fixed fb_batch_router.py")

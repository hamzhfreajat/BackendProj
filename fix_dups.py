import codecs
import re

with codecs.open('seed_categories.py', 'r', 'utf-8') as f:
    content = f.read()

# I will replace all occurrences of `(\b420` -> `(99420` where it's the start of the tuple.
# Same for 430, 440, 450, 460, 470, 480.
# Wait, only the child IDs (4201, 4301 etc) need to be replaced, NOT the parent IDs (420, 430 ...).
# The parent IDs are defined as `(420, 4, ...)` -> do not change!
# the children are defined as `(4201, 420, ...)` -> change to `(994201, 420, ...)`

lines = content.split('\n')
new_lines = []
for line in lines:
    # Only replace if line starts with space and (420x, or (430x
    match = re.search(r'^(\s*)\((4[2-8]0\d+),\s*(4[2-8]0),', line)
    if match:
        old_id = match.group(2)
        new_id = "99" + old_id
        line = line.replace(f"({old_id},", f"({new_id},", 1)
    new_lines.append(line)

with codecs.open('seed_categories.py', 'w', 'utf-8') as f:
    f.write('\n'.join(new_lines))

print("Fixed duplicates in seed_categories.py")

import re

with open('seed_categories.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        match = re.search(r'\((\d+),', line)
        if match:
            num = int(match.group(1))
            if num > 2147483647:
                print(f"Line {i}: {line.strip()}")

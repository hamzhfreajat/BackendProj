with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if ', 5, ' in line]
with open('5.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

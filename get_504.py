with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if '(504,' in line.replace(' ','') or '(5,' in line.replace(' ','')]
with open('504.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

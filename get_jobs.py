with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f if '(6,' in line or '(601,' in line or '(602,' in line or '(7,' in line]

with open('6_and_7.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

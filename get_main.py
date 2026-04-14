with open('seed_categories.py', 'r', encoding='utf-8') as f:
    lines = [ln.strip() for ln in f if ',  None,' in ln or ', None,' in ln]

with open('main_cats.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

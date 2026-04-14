with open('seed_categories.py', 'r', encoding='utf-8') as f:
    for line in f:
        if '10010101' in line or 'كلاب حراسة' in line:
            print(line.strip())

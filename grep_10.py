with open('seed_categories.py', 'r', encoding='utf-8') as f:
    for line in f:
        # Check if the line defines an ID starting with 10 (length 4), e.g., 10xx
        if line.strip().startswith('(10'):
            # Only print first few to see pattern
            print(line.strip())

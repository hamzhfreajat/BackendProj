import re
try:
    content = open('seed_error_utf8.log', encoding='utf-16le').read()
    # Looks for the SQLAlchemy parameters
    # E.g. IntegrityError: UNIQUE constraint failed: categories.id
    # [SQL: INSERT INTO categories (id, parent_id, ...) VALUES (?, ?, ...)]
    # [parameters: (4201, 20, ...)]
    
    matches_id = re.findall(r'UNIQUE constraint failed.*?\n.*?parameters.*?\[?\((.*?)\)', content, re.IGNORECASE | re.DOTALL)
    if not matches_id:
        print("Fallback parsing...")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "IntegrityError" in line:
                print("Error line:", line.encode('ascii', 'ignore').decode('ascii'))
            if "parameters" in line:
                print("Params line:", line.encode('ascii', 'ignore').decode('ascii'))
    else:
        print("Failed parameters:", matches_id[-1].encode('ascii', 'ignore').decode('ascii'))
except Exception as e:
    print(f"Failed to parse error log: {e}")

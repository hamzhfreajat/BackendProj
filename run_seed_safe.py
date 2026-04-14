import sys
import traceback

try:
    from seed_categories import seed
    seed()
except Exception as e:
    with open('seed_error.txt', 'w', encoding='utf-8') as f:
        f.write("OUTER ERROR:\\n" + str(e))

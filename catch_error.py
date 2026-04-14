from seed_categories import seed
import traceback

try:
    seed()
except Exception as e:
    error_str = str(e).encode('ascii', errors='ignore').decode('ascii')
    print("DB ERROR DETAILS:")
    print(error_str)

import sys
filepath = r"D:\open\classifieds-app\backend\main.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We need to remove the logging block from get_ads_count.
# get_ads_count is defined around line 1250-1300
part_to_remove = '''
        # Log the search query and results count
        try:
            from models import SearchQueryLog
            log_entry = SearchQueryLog(
                query_text=search.strip(),
                results_count=len(ranked_ad_ids),
                user_id=current_user.id if hasattr(current_user, 'id') else None
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error logging search: {e}")
'''

# Find get_ads_count
idx = content.find('def get_ads_count')
if idx != -1:
    before = content[:idx]
    after = content[idx:]
    after = after.replace(part_to_remove, "", 1)
    content = before + after
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed get_ads_count")

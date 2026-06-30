import sys
filepath = r"D:\open\classifieds-app\backend\main.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the autocomplete logging
old_code = '''
        # Save raw query log since autocomplete was removed and this is called on submit
        if q and len(q.strip()) > 1:
            try:
                log_entry = SearchQueryLog(query_text=q.strip())
                db.add(log_entry)
                db.commit()
            except Exception as log_err:
                db.rollback()
                print(f"Error saving search log: {log_err}")
'''
if old_code in content:
    content = content.replace(old_code, "")
    print("Removed logging from autocomplete")

# Add logging to read_ads
import re
read_ads_part = '''
    if search:
        ranked_ad_ids = SearchService.search_properties(db, search, limit=1000)'''

new_read_ads = '''
    if search:
        ranked_ad_ids = SearchService.search_properties(db, search, limit=1000)
        
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
if read_ads_part in content:
    content = content.replace(read_ads_part, new_read_ads)
    print("Added logging to read_ads")
else:
    print("Could not find read_ads part")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

import sys
import re

filepath = r"D:\open\classifieds-app\backend\main.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# We want to replace the return statement of get_search_logs
old_return = 'return [{"id": l.id, "query_text": l.query_text, "results_count": l.results_count, "created_at": l.created_at.isoformat()} for l in logs]'
new_return = '''return [{
        "id": l.id, 
        "query_text": l.query_text, 
        "results_count": l.results_count, 
        "created_at": l.created_at.isoformat(),
        "user": {"id": l.user.id, "name": f"{l.user.first_name or ''} {l.user.last_name or ''}".strip() or l.user.name, "email": l.user.email} if l.user else None
    } for l in logs]'''

if old_return in content:
    new_content = content.replace(old_return, new_return)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Updated get_search_logs in main.py")
else:
    print("Could not find the return statement to replace.")

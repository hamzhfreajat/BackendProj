import sys, os
sys.path.insert(0, os.path.abspath('d:/open/classifieds-app/backend'))
from database import SessionLocal
import models

db = SessionLocal()

print('--- API Logs for User 268 ---')
# In models, user_id is a String for some reason, let's just query everything and filter in python to avoid casting issues
logs = db.query(models.ApiHitLog).order_by(models.ApiHitLog.created_at.desc()).limit(100).all()
for log in logs:
    if str(log.user_id) == '268' and ('api/ads' in log.endpoint_name or log.status_code >= 400):
        print(f'[{log.created_at}] {log.endpoint_name} - {log.status_code}')
        if hasattr(log, 'error_message') and log.error_message:
            print(f'  Error: {log.error_message}')

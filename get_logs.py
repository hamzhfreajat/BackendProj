
import sys
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
from models import AITrainingLog
import json
db = SessionLocal()
logs = db.query(AITrainingLog).order_by(AITrainingLog.processed_at.desc()).limit(17).all()
for l in logs:
    text = l.raw_text[:40].replace('\n', ' ') if l.raw_text else 'N/A'
    print(f'[{l.processed_at}] {l.status} | {text} | {l.rejection_reason}')


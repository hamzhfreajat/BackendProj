import sys
sys.path.append('d:/open/classifieds-app/backend')
from database import SessionLocal
from models import Ad, AITrainingLog
db = SessionLocal()
print('Total ads:', db.query(Ad).count())
print('Total AI logs:', db.query(AITrainingLog).count())

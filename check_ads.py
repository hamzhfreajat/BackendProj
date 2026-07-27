import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session
from sqlalchemy import or_

db: Session = SessionLocal()

phrases = ['قهوة الدلة', 'بن العميد', 'صالة السفير', 'مستشفى الرويال', 'الونك والفلاتر', 'منتزه الأميرة سلمى', 'كازية عاشور', 'جنوب كلية', 'قصر العوادين', 'صالة الهرمل', 'شارع البتراء', 'كمباوند الأمعري', 'منطقة فلل']

for p in phrases:
    ads = db.query(models.Ad).filter(or_(models.Ad.description.like(f'%{p}%'), models.Ad.raw_description.like(f'%{p}%'))).all()
    print(f"{p.encode('utf-8').decode('cp1252', 'ignore')}: {len(ads)} ads")

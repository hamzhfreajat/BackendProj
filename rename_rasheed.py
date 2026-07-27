import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

# We know from our previous query that 'الرشيد' is region ID 1722
reg = db.query(models.Region).filter(models.Region.id == 1722).first()
if reg:
    reg.name_ar = 'ضاحية الرشيد'
    
    # Update ads
    ads = db.query(models.Ad).filter(models.Ad.location.like('%الرشيد%')).all()
    count = 0
    for ad in ads:
        if 'عمان, الرشيد' in ad.location:
            ad.location = ad.location.replace('عمان, الرشيد', 'عمان, ضاحية الرشيد')
            count += 1
            
    db.commit()
    print("Success")
else:
    print("Region 1722 not found.")

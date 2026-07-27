import sys, os
sys.path.append(os.path.dirname(os.path.abspath('models.py')))
from database import SessionLocal
import models
from sqlalchemy.orm import Session

db: Session = SessionLocal()

# 1. Delete all existing rubbish data
db.query(models.RegionAlias).delete()
db.commit()

# 2. Re-insert the correct aliases
merges = [
    {"keep_id": 1628, "bad_names": ["ايدون", "أيدون"]},
    {"keep_id": 1543, "bad_names": ["الجبيهه", "الحبيهة"]},
    {"keep_id": 1746, "bad_names": ["الصوفية"]},
    {"keep_id": 1742, "bad_names": ["ديرغبار"]},
    {"keep_id": 1852, "bad_names": ["شارع عبدالله غوشة"]},
    {"keep_id": 261,  "bad_names": ["الرهبات الوردية", "حي الرهبات"]},
    {"keep_id": 622,  "bad_names": ["عين والمعمريه", "عين والمعرية"]},
    {"keep_id": 1720, "bad_names": ["أم زوتينة"]},
    {"keep_id": 1703, "bad_names": ["الذهيبه الشرقيه"]},
    {"keep_id": 116,  "bad_names": ["الهاشمي شمالي"]},
    {"keep_id": 423,  "bad_names": ["العالوك, المسرّة"]},
    {"keep_id": 515,  "bad_names": ["جبيل"]},
    {"keep_id": 1763, "bad_names": ["المنطقة الرياضية"]},
    {"keep_id": 286,  "bad_names": ["بشري"]},
    {"keep_id": 281,  "bad_names": ["نعيمة, طريق النعيمه"]},
    {"keep_id": 422,  "bad_names": ["الكمشه"]},
    {"keep_id": 602,  "bad_names": ["الزيتونه, حي الزيتونة"]},
    {"keep_id": 151,  "bad_names": ["حي البتراء"]},
    {"keep_id": 293,  "bad_names": ["اسكان الاطباء"]},
    {"keep_id": 99,   "bad_names": ["الرونق, حي الصناعة"]},
    {"keep_id": 1600, "bad_names": ["قصبة اربد"]},
    {"keep_id": 183,  "bad_names": ["قصبة جرش"]},
    {"keep_id": 465,  "bad_names": ["منطقة الفلاح"]},
    {"keep_id": 1722, "bad_names": ["ضاحية زرشيد"]}
]

for merge in merges:
    keep_id = merge["keep_id"]
    # Verify the target region exists
    if not db.query(models.Region).filter(models.Region.id == keep_id).first():
        print(f"Region ID {keep_id} not found, skipping...")
        continue
        
    for bad_name in merge["bad_names"]:
        alias = models.RegionAlias(region_id=keep_id, alias_name=bad_name)
        db.add(alias)

db.commit()
print("Aliases have been correctly restored with UTF-8 encoding!")

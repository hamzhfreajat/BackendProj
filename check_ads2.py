from database import SessionLocal
import models
import json
db = SessionLocal()
ad = db.query(models.Ad).filter(models.Ad.id == 21076).first()
print('Phone in attributes:', ad.attributes.get('phone_number') if ad.attributes else None)
print('Description contains phone:', '0787224854' in (ad.description or ''))
print('Raw Description contains phone:', '0787224854' in (ad.raw_description or ''))
print('Title contains phone:', '0787224854' in (ad.title or ''))

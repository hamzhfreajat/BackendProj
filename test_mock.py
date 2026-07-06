import sys
import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.attributes import flag_modified

Base = declarative_base()

class AdMock(Base):
    __tablename__ = 'ads_mock'
    id = Column(Integer, primary_key=True)
    attributes = Column(JSONB)

engine = create_engine('sqlite:///:memory:')
# Using SQLite for a quick test, though JSONB is postgres specific. Let's just use Python dict directly.
class MockAd:
    def __init__(self):
        self.attributes = {"transaction_type": "Sale"}

db_ad = MockAd()

update_dict = {
    "image_urls": ["url1", "url2", "url3"],
    "attributes": {"transaction_type": "Sale"}
}

image_urls_updated = False
if "image_urls" in update_dict:
    image_urls = update_dict.pop("image_urls")
    image_urls_updated = True

attributes = update_dict.get("attributes") or {}
if image_urls_updated:
    attributes["image_urls"] = image_urls

update_dict["attributes"] = attributes

for key, value in update_dict.items():
    if hasattr(db_ad, key) and key not in ["id", "user_id", "created_at"]:
        setattr(db_ad, key, value)

print("db_ad.attributes after update:", db_ad.attributes)

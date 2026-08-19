import os
from dotenv import load_dotenv

load_dotenv('d:/open/classifieds-app/backend/.env')

from sqlalchemy import create_engine, or_, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_name = os.getenv('DB_NAME', 'classifieds')
    db_port = os.getenv('DB_PORT', '5432')
    DATABASE_URL = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import sys
sys.path.append('d:/open/classifieds-app/backend')
from models import Ad, User

db = SessionLocal()
try:
    phone = '0786688634'
    query = text("SELECT id, description, raw_description, attributes FROM ads WHERE description LIKE :p OR raw_description LIKE :p OR attributes::text LIKE :p")
    
    result = db.execute(query, {'p': f'%{phone}%'}).fetchall()
    
    with open('d:/open/classifieds-app/backend/found_ads.txt', 'w', encoding='utf-8') as f:
        f.write('Found ads with text/attributes match:\\n')
        for row in result:
            f.write(f'Ad ID: {row[0]}, attrs: {row[3]}\\n')
            
        query2 = text("SELECT id, phone, mobile_number FROM users WHERE phone LIKE :p OR mobile_number LIKE :p")
        users = db.execute(query2, {'p': f'%{phone}%'}).fetchall()
        f.write('Found users:\\n')
        for u in users:
            f.write(f'User ID: {u[0]}, phone: {u[1]}, mobile: {u[2]}\\n')
except Exception as e:
    with open('d:/open/classifieds-app/backend/found_ads.txt', 'w', encoding='utf-8') as f:
        f.write(f'Error: {e}\\n')
finally:
    db.close()

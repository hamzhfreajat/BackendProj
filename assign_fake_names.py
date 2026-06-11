import os
import random
from database import SessionLocal
import models
import sys
sys.stdout.reconfigure(encoding='utf-8')

FIRST_NAMES = [
    "محمد", "أحمد", "يوسف", "محمود", "عمر", "علي", "عبدالله", "سليمان", "خالد", "حسن",
    "وليد", "طارق", "فهد", "بدر", "رامي", "فراس", "عمار", "ياسر", "سعد", "ماجد",
    "فاطمة", "سارة", "نور", "ليلى", "مريم", "رشا", "هند", "عبير", "منى", "رنا"
]

LAST_NAMES = [
    "الخطيب", "المصري", "العوضي", "الحداد", "النجار", "محمود", "إبراهيم", "سعيد", "صالح", "حسن",
    "الحياري", "الزعبي", "الخصاونة", "المجالي", "العبادي", "بني هاني", "عطية", "الرفاعي", "منصور", "شاهين"
]

from sqlalchemy import text

def generate_fake_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def run():
    db = SessionLocal()
    try:
        # Update scraper users
        sql_update_scraper = text("""
            UPDATE users 
            SET username = :new_name, full_name = :new_name 
            WHERE email = 'ai_scraper@system.com' OR username = 'AI Auto Scraper' OR username = 'مستخدم'
        """)
        db.execute(sql_update_scraper, {"new_name": generate_fake_name()})
        
        # Select users with no username or full_name
        sql_select_nameless = text("""
            SELECT id FROM users 
            WHERE username IS NULL OR username = '' OR full_name IS NULL OR full_name = ''
        """)
        nameless_users = db.execute(sql_select_nameless).fetchall()
        
        sql_update_single = text("UPDATE users SET username = :new_name, full_name = :new_name WHERE id = :id")
        for u in nameless_users:
            new_name = generate_fake_name()
            db.execute(sql_update_single, {"new_name": new_name, "id": u[0]})
            
        db.commit()
        print(f"Done! Updated scraper users and {len(nameless_users)} nameless users with fake names.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run()

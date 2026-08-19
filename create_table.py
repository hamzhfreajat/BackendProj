import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from database import Base, engine
import models

def create_tables():
    print("Creating blocked_phone_numbers table...")
    models.BlockedPhoneNumber.__table__.create(bind=engine, checkfirst=True)
    print("Table created successfully!")

if __name__ == "__main__":
    create_tables()

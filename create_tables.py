import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from models import Base

def main():
    print("Creating missing tables...")
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    main()

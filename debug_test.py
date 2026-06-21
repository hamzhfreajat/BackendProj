from database import SessionLocal
from models import City
from main import norm_str, norm_col

db = SessionLocal()
c_norm = norm_str('جرش')
city = db.query(City).filter(norm_col(City.name_ar) == c_norm).first()

with open('debug_output.txt', 'w', encoding='utf-8') as f:
    f.write('City found: ' + (city.name_ar if city else 'None'))

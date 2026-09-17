import codecs
import sys
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
from database import SessionLocal
from models import Category

db = SessionLocal()

RELATED = {
    'جايكو': 'شيري',
    'جاي ام اي في': 'جاي ام سي',
    'دي اف اس كي': 'دونج فينج',
    'سيريس': 'دي اف ام',
    'ساوايست': 'ميتسوبيشي',
    'زد إكس اوتو': 'جريت وول',
    'كايي': 'شيري',
    'في جي في': 'سينوترك',
    'اس دبليو ام': 'بريليانس',
    'هونغهاي': 'شانجان',
    'يودو': 'فاو',
    'لينج بوكس': 'جاك',
    'ريهاي': 'زوتي',
    'ربدان': 'بي واي دي',
    'آي إم': 'ام جي',
    'اخرى': 'تويوتا'
}

all_cats = db.query(Category).filter(Category.parent_id.in_([101, 102])).all()
# Print out all the names in db just to check whitespace
cat_dict = {}
for c in all_cats:
    clean_name = c.name.strip()
    cat_dict[clean_name] = c

for missing_name, related_name in RELATED.items():
    if missing_name in cat_dict and related_name in cat_dict:
        missing_cat = cat_dict[missing_name]
        related_cat = cat_dict[related_name]
        print(f"Match found: {missing_name} -> {related_name}")
        if missing_cat.icon_name is None and related_cat.icon_name is not None:
            missing_cat.icon_name = related_cat.icon_name
            db.commit()
            print(f"Updated {missing_name} with {related_name}'s icon")
    else:
        if missing_name not in cat_dict:
            print(f"Missing name not found in db: {missing_name}")
        if related_name not in cat_dict:
            print(f"Related name not found in db: {related_name}")

db.close()

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

DATABASE_URL = "postgresql://cmnynjgg70001aumle0zkfovm:z9l0aau7lAGSmmCGghGwKNbP@178.104.204.148:9000/cmnynjgg90003aumlerff4j9q"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Load all categories
res = db.execute(text("SELECT id, name, parent_id FROM category")).fetchall()
categories = {row[0]: {'name': row[1], 'parent_id': row[2]} for row in res}

commercial_keywords = ['تجاري', 'مكتب', 'مكاتب', 'مخزن', 'مخازن', 'عياد', 'عيادات', 'معرض', 'معارض', 'مستودع', 'صناعي', 'مبنى', 'مباني', 'مجمع', 'محل', 'محلات']

def get_form_type(cat_id):
    current_id = cat_id
    while current_id:
        if current_id in [311, 10311]: return 'Commercial'
        
        cat = categories.get(current_id)
        if not cat: break
        
        name = cat['name']
        if any(kw in name for kw in commercial_keywords): return 'Commercial'
        if 'دراج' in name or 'دباب' in name: return 'Motorcycle'
        if 'قطع غيار' in name or 'إكسسوارات' in name: return 'AutoParts'
        if 'لوحات' in name or 'أرقام سيارات' in name: return 'LicensePlates'
        if 'حيوانات' in name or 'قطط' in name or 'كلاب' in name or 'طيور' in name: return 'Pets'
        
        if current_id == 306: return 'Apartment'
        current_id = cat['parent_id']
    return 'Generic'

# Update Drafts
drafts = db.execute(text("SELECT id, category_id, attributes FROM draft_ad")).fetchall()
for d in drafts:
    d_id, cat_id, attrs = d
    if cat_id:
        form_type = get_form_type(cat_id)
        if attrs is None: attrs = {}
        attrs['form_type'] = form_type
        db.execute(text("UPDATE draft_ad SET attributes = :attr WHERE id = :id"), {"attr": json.dumps(attrs, ensure_ascii=False), "id": d_id})

# Update Ads
ads = db.execute(text("SELECT id, category_id, attributes FROM ad")).fetchall()
for a in ads:
    a_id, cat_id, attrs = a
    if cat_id:
        form_type = get_form_type(cat_id)
        if attrs is None: attrs = {}
        attrs['form_type'] = form_type
        db.execute(text("UPDATE ad SET attributes = :attr WHERE id = :id"), {"attr": json.dumps(attrs, ensure_ascii=False), "id": a_id})

db.commit()
print("Successfully patched all drafts and ads with form_type!")

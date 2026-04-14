from database import SessionLocal
from models import Category

db = SessionLocal()
orphans = db.query(Category).filter(Category.parent_id == None, Category.id > 1000).all()

oppo_id = 7886
xiaomi_id = 7884
infinix_id = 12219

fixed = 0
for o in orphans:
    name = (o.name or "").lower().strip()
    if not name:
        continue
        
    assigned = None
    
    if name == 'other':
        # Don't assign 'other' blindly
        continue
        
    if 'infinix' in name or name.startswith('hot') or name.startswith('smart') or name.startswith('zero'):
        assigned = infinix_id
    elif 'oppo' in name or name.startswith('find') or name.startswith('reno') or name.startswith('k') or name.startswith('r') or name.startswith('a') or name.startswith('f') or name.startswith('ace'):
        assigned = oppo_id
    elif 'xiaomi' in name or 'redmi' in name or 'poco' in name or 'black shark' in name or 'mix' in name or name.startswith('mi') or name[0].isdigit() or name.startswith('s2') or name.startswith('note'):
        assigned = xiaomi_id

    if assigned:
        o.parent_id = assigned
        fixed += 1
    else:
        print(f"Could not classify: {name}")

db.commit()
print(f"Successfully reparented {fixed} orphan phone models in the database!")
db.close()

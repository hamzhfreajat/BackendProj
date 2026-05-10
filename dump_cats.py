import models
from database import SessionLocal

db = SessionLocal()
try:
    cats = db.query(models.Category).all()
    
    def get_children(pid, level=0):
        res = []
        for c in cats:
            if c.parent_id == pid:
                res.append((level, c))
                res.extend(get_children(c.id, level + 1))
        return res

    all_res = get_children(2) + get_children(3)
    
    with open('res2.txt', 'w', encoding='utf-8') as f:
        for level, c in all_res:
            f.write('  ' * level + "- " + c.name + '\n')
finally:
    db.close()

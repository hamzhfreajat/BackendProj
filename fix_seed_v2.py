def fix_seed():
    with open('seed_categories.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out = []
    for line in lines:
        out.append(line)
        if '(716, 7' in line and 'أخرى' in line:
            # this is the last valid list item
            break
            
    out.append(']\n\n')
    
    seed_func = """
def seed():
    from database import SessionLocal
    import models
    db = SessionLocal()
    
    try:
        # First Pass: Parents
        for cat in CATEGORIES:
            if cat[1] is None:
                slugs = cat[7] if len(cat) > 7 else None
                existing = db.query(models.Category).filter(models.Category.id == cat[0]).first()
                if existing:
                    existing.name = cat[2]
                    existing.description = cat[3]
                    existing.icon_name = cat[4]
                    existing.color_hex = cat[5]
                    existing.tag = cat[6]
                    existing.slugs = slugs
                else:
                    new_cat = models.Category(
                        id=cat[0], parent_id=cat[1], name=cat[2],
                        description=cat[3], icon_name=cat[4], color_hex=cat[5],
                        tag=cat[6], slugs=slugs
                    )
                    db.add(new_cat)
        db.flush()

        # Second Pass: Level 1
        for cat in CATEGORIES:
            if cat[1] is not None:
                parent = db.query(models.Category).filter(models.Category.id == cat[1]).first()
                if parent and parent.parent_id is None:
                    slugs = cat[7] if len(cat) > 7 else None
                    existing = db.query(models.Category).filter(models.Category.id == cat[0]).first()
                    if existing:
                        existing.name = cat[2]
                        existing.icon_name = cat[4]
                        existing.slugs = slugs
                    else:
                        new_cat = models.Category(
                            id=cat[0], parent_id=cat[1], name=cat[2],
                            description=cat[3], icon_name=cat[4], color_hex=cat[5],
                            tag=cat[6], slugs=slugs
                        )
                        db.add(new_cat)
        db.flush()

        # Third Pass: Level 2
        for cat in CATEGORIES:
            if cat[1] is not None:
                parent = db.query(models.Category).filter(models.Category.id == cat[1]).first()
                if parent and parent.parent_id is not None:
                    grandparent = db.query(models.Category).filter(models.Category.id == parent.parent_id).first()
                    if grandparent and grandparent.parent_id is None:
                        slugs = cat[7] if len(cat) > 7 else None
                        existing = db.query(models.Category).filter(models.Category.id == cat[0]).first()
                        if existing:
                            existing.name = cat[2]
                            existing.icon_name = cat[4]
                            existing.slugs = slugs
                        else:
                            new_cat = models.Category(
                                id=cat[0], parent_id=cat[1], name=cat[2],
                                description=cat[3], icon_name=cat[4], color_hex=cat[5],
                                tag=cat[6], slugs=slugs
                            )
                            db.add(new_cat)
        db.flush()

        # Fourth Pass: Level 3
        for cat in CATEGORIES:
            if cat[1] is not None:
                parent = db.query(models.Category).filter(models.Category.id == cat[1]).first()
                if parent and parent.parent_id is not None:
                    grandparent = db.query(models.Category).filter(models.Category.id == parent.parent_id).first()
                    if grandparent and grandparent.parent_id is not None:
                        slugs = cat[7] if len(cat) > 7 else None
                        existing = db.query(models.Category).filter(models.Category.id == cat[0]).first()
                        if existing:
                            existing.name = cat[2]
                            existing.icon_name = cat[4]
                            existing.slugs = slugs
                        else:
                            new_cat = models.Category(
                                id=cat[0], parent_id=cat[1], name=cat[2],
                                description=cat[3], icon_name=cat[4], color_hex=cat[5],
                                tag=cat[6], slugs=slugs
                            )
                            db.add(new_cat)
                            
        db.commit()
        print(f"Categories seeded successfully. Total in list: {len(CATEGORIES)}")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    seed()
"""
    
    with open('seed_categories.py', 'w', encoding='utf-8') as f:
        f.write("".join(out) + seed_func)

fix_seed()

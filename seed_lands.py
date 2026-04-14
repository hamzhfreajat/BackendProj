import models
from database import engine, SessionLocal
from sqlalchemy import text

models.Base.metadata.create_all(bind=engine)

def seed_lands():
    db = SessionLocal()
    
    # 1. We know Governorates are inside `cities` table
    amman = db.query(models.City).filter(models.City.name_ar == 'عمان').first()
    irbid = db.query(models.City).filter(models.City.name_ar == 'إربد').first()
    
    if not irbid:
        print("Run seed_locations.py first!")
        return

    # Delete old directorates for clean seed
    try:
        db.execute(text("DELETE FROM neighborhood_sectors"))
        db.execute(text("DELETE FROM basins"))
        db.execute(text("DELETE FROM villages"))
        db.execute(text("DELETE FROM directorates"))
        db.commit()
    except Exception:
        db.rollback()

    # --- IRBID DIRECTORATES (From our API ping) ---
    irbid_directorates = [
        "اراضي المزار الشمالي (18)",
        "اراضي الرمثا (12)",
        "اراضي الشونة الشمالية (14)",
        "اراضي الطيبة (16)",
        "اراضي بني كنانة (15)",
        "اراضي دير ابي سعيد (13)",
        "اراضي اربد (9)"
    ]

    for d_name in irbid_directorates:
        db_dir = models.Directorate(city_id=irbid.id, name_ar=d_name)
        db.add(db_dir)
        db.flush()
        
        # Villages
        if 'اربد (9)' in d_name:
            villages = ['اربد (171)', 'البارحة (54)', 'حوارة', 'بشرى', 'سال']
        elif 'الرمثا' in d_name:
            villages = ['الرمثا المدينة (21)', 'الطرة (18)', 'الشجرة']
        else:
            villages = [d_name.replace('اراضي', 'قرية')]
            
        for v_name in villages:
            db_vil = models.Village(directorate_id=db_dir.id, name_ar=v_name)
            db.add(db_vil)
            db.flush()
            
            # Basins for Irbid City
            if '171' in v_name:
                basins = ['حوض 1 البلد', 'حوض 2 القصيلة', 'حوض 3 البارحة الغربي', 'حوض 4 زبدة', 'حوض 5 الجامعة']
                for b_name in basins:
                    db_bas = models.Basin(village_id=db_vil.id, name_ar=b_name)
                    db.add(db_bas)
                    db.flush()
                    
                    # Neighborhoods
                    neighborhoods = ['الحي الشرقي', 'الحي الجنوبي', 'حي التركمان']
                    for n_name in neighborhoods:
                        db_neigh = models.NeighborhoodSector(basin_id=db_bas.id, name_ar=n_name)
                        db.add(db_neigh)
                        
    db.commit()
    db.close()
    print("Seeded Irbid Land Locations successfully!")

if __name__ == '__main__':
    seed_lands()

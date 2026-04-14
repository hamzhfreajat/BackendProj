from database import SessionLocal
import models
from seed_categories import CATEGORIES

def fix_icons():
    db = SessionLocal()
    try:
        # Step 1: Repair the damage to ID 4 (Mobiles) by pulling from seed_categories
        def recursive_fix(node_list, parent_id_val=None):
            for cat in node_list:
                db_cat = db.query(models.Category).filter(models.Category.name == cat['name'], models.Category.parent_id == parent_id_val).first()
                if db_cat and 'iconName' in cat:
                    db_cat.icon_name = cat['iconName']
                if db_cat and 'subcategories' in cat:
                    recursive_fix(cat['subcategories'], db_cat.id)

        # Pull original ID 4 data from memory dictionary
        for root in CATEGORIES:
            if "موبايلات" in root['name']:
                 db_root = db.query(models.Category).filter(models.Category.name == root['name']).first()
                 if db_root and 'iconName' in root:
                      db_root.icon_name = root['iconName']
                 if db_root and 'subcategories' in root:
                      recursive_fix(root['subcategories'], db_root.id)
                      
        # Step 2: Assign proper fine-grained Emojis to Real Estate (IDs 2 and 3)
        real_estate_map = {
            "سكني": "🏘️",
            "شقق": "🏢",
            "فلل": "🏰",
            "رووف": "🌇",
            "دوبلكس": "🏙️",
            "شاليهات": "🏖️",
            "عمارات": "🏬",
            "سكن مشترك": "🏠",
            "غرف مشتركة": "🛏️",
            "غرف مستقلة": "🚪",
            "سرير": "🛏️",
            "تجاري": "🏪",
            "اراضي": "🏞️",
            "أراضي": "🏞️",
            "أراضي زراعية": "🚜",
            "أراضي تجارية": "🏪",
            "أراضي سكنية": "🏘️",
            "أراضي صناعية": "🏭",
            "مزارع": "🚜",
            "مكاتب": "💼",
            "عيادات": "🏥",
            "مستودعات": "🏭",
            "محلات": "🛍️",
            "استوديو": "🛋️",
            "ستوديو": "🛋️",
            "بيوت مستقلة": "🏡",
            "طابق كامل": "🏢",
            "بيوت ريفية": "🛖"
        }
        
        def get_real_estate_emoji(name, default_fallback):
            # Check for the best match using longest keys first
            best_match = None
            max_len = 0
            for k, v in real_estate_map.items():
                if k in name and len(k) > max_len:
                    best_match = v
                    max_len = len(k)
            if best_match: return best_match
            if "بيع" in name: return "🏡"
            if "ايجار" in name: return "🔑"
            return default_fallback
            
        real_estate_roots = db.query(models.Category).filter(models.Category.id.in_([2, 3])).all()
        for root in real_estate_roots:
            # Root emoji
            if "بيع" in root.name: root.icon_name = "🏡"
            elif "ايجار" in root.name or "إيجار" in root.name: root.icon_name = "🔑"
            
            l2_cats = db.query(models.Category).filter(models.Category.parent_id == root.id).all()
            for l2 in l2_cats:
                l2.icon_name = get_real_estate_emoji(l2.name, "🏠")
                
                l3_cats = db.query(models.Category).filter(models.Category.parent_id == l2.id).all()
                for l3 in l3_cats:
                    l3.icon_name = get_real_estate_emoji(l3.name, l2.icon_name)
                    
                    l4_cats = db.query(models.Category).filter(models.Category.parent_id == l3.id).all()
                    for l4 in l4_cats:
                        l4.icon_name = get_real_estate_emoji(l4.name, l3.icon_name)
                        
        db.commit()
        print("Restored Mobiles logic and successfully assigned rich Emojis to Real Estate!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_icons()

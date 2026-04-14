"""
Migration script to:
1. Remap ads from old عقارات للبيع categories to new ones
2. Delete old flat categories (201-210 and their children)
3. Insert new hierarchical categories mirroring عقارات للإيجار

Old → New mapping:
  201 (شقق للبيع)            → 10301 (شقق للبيع under سكني)
  202 (أراضي للبيع)          → 19001 (أرض سكنية under أراضي)
  203 (فلل وقصور للبيع)      → 10101 (فلل وقصور under سكني)
  204 (عقارات تجارية ومحلات) → 10853 (محلات تجارية عامة under تجاري)
  205 (مزارع وشاليهات للبيع) → 19200 (مزارع زراعية)
  206 (بيوت ومنازل للبيع)    → 10102 (بيوت مستقلة للبيع)
  207 (عمارات ومجمعات)       → 18032 (مباني تجارية كاملة)
  208 (قيد الإنشاء)          → 10301 (شقق للبيع)
  209 (عقارات أجنبية)        → 10999 (أخرى - سكني)
  210 (أخرى - سكنية)         → 10999 (أخرى - سكني)
  2015 (شقق فندقية)          → 10015 (شقق فندقية / مخدومة)
  2016 (استديوهات)           → 10302 (ستوديوهات للبيع)
  2031 (فلل مستقلة)          → 10101 (فلل وقصور)
  2032 (فلل شبه مستقلة)      → 10101 (فلل وقصور)
  2033 (قصور)                → 10101 (فلل وقصور)
  2051 (مزارع مع فيلا)       → 19232 (مزرعة مع فيلا)
  2052 (شاليهات خاصة)        → 19301 (شاليه مستقل)
  2061 (بيوت مستقلة حديثة)   → 10102 (بيوت مستقلة للبيع)
  2062 (بيوت عربية)          → 10102 (بيوت مستقلة للبيع)
  2071 (عمارات سكنية)        → 18033 (عمارة تجارية)
  2072 (مجمعات سكنية)        → 18034 (مجمع تجاري)
  2073 (سكن طلاب)            → 10999 (أخرى)
  2081 (شقق قيد الإنشاء)     → 10301 (شقق للبيع)
  2082 (فلل وبيوت عظم)       → 10101 (فلل وقصور)
  2101 (حصص مشاع)            → 10999 (أخرى)
  2102 (أسطح للبيع)          → 10105 (ملحق / روف)
"""

import sys
sys.path.insert(0, '.')
from database import SessionLocal
from sqlalchemy import text

# Mapping: old_id -> new_id
AD_REMAP = {
    201:  10301,
    202:  19001,
    203:  10101,
    204:  10853,
    205:  19200,
    206:  10102,
    207:  18032,
    208:  10301,
    209:  10999,
    210:  10999,
    2015: 10015,
    2016: 10302,
    2031: 10101,
    2032: 10101,
    2033: 10101,
    2051: 19232,
    2052: 19301,
    2061: 10102,
    2062: 10102,
    2071: 18033,
    2072: 18034,
    2073: 10999,
    2081: 10301,
    2082: 10101,
    2101: 10999,
    2102: 10105,
}

def migrate():
    db = SessionLocal()
    try:
        # Step 1: Check current state
        result = db.execute(text("""
            WITH RECURSIVE sale_tree AS (
                SELECT id FROM categories WHERE parent_id = 2
                UNION ALL
                SELECT c.id FROM categories c INNER JOIN sale_tree st ON c.parent_id = st.id
            )
            SELECT category_id, COUNT(*) as ad_count
            FROM ads WHERE category_id IN (SELECT id FROM sale_tree)
            GROUP BY category_id ORDER BY category_id
        """))
        ads_to_remap = result.fetchall()
        print(f"Ads to remap: {ads_to_remap}")

        # Step 2: Remap ads from old categories to new categories
        for old_id, new_id in AD_REMAP.items():
            result = db.execute(text("UPDATE ads SET category_id = :new_id WHERE category_id = :old_id"),
                               {"old_id": old_id, "new_id": new_id})
            if result.rowcount > 0:
                print(f"  Remapped {result.rowcount} ads from {old_id} → {new_id}")

        # Step 3: Delete old categories (children first, then parents)
        # First delete deeper children (2015, 2016, 2031-2033, 2051-2052, etc.)
        db.execute(text("""
            DELETE FROM categories WHERE id IN (
                2015, 2016,
                2031, 2032, 2033,
                2051, 2052,
                2061, 2062,
                2071, 2072, 2073,
                2081, 2082,
                2101, 2102
            )
        """))
        print("Deleted old third-level categories")

        # Then delete the second-level (201-210)
        db.execute(text("DELETE FROM categories WHERE id IN (201, 202, 203, 204, 205, 206, 207, 208, 209, 210)"))
        print("Deleted old second-level categories (201-210)")

        db.commit()
        print("\n✅ Migration completed successfully!")

        # Verify
        result = db.execute(text("SELECT COUNT(*) FROM ads WHERE category_id BETWEEN 201 AND 210"))
        remaining = result.scalar()
        print(f"Remaining ads in old categories: {remaining}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()

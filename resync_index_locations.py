"""
Makes the search index agree with each ad's own location.

The index used to guess an ad's area from words in its text (see
search_service.resolve_ad_location for the story). relocate_misfiled_ads.py
repaired the ads whose *location* had been overwritten with such a guess, but an
ad whose location was right could still carry a guessed area in its index row,
and the website and the app's search read the area from the index. This sets
city_id and region_id in the index from the ad's location for every ad.

Run from the backend folder:

    python resync_index_locations.py                 # dry run: prints what would change
    python resync_index_locations.py --apply         # writes index_location_backup_<time>.json, then updates
    python resync_index_locations.py --rollback index_location_backup_<time>.json
"""
import argparse
import collections
import json
import sys
import time

BATCH = 500
RETRIES = 5


def build_plan(db):
    import models
    from search_service import resolve_ad_location

    cities = {c.id: c.name_ar for c in db.query(models.City).all()}
    regions = {r.id: r.name_ar for r in db.query(models.Region).all()}
    Ad, Index = models.Ad, models.AdSearchIndex
    rows = db.query(Ad.id, Ad.location, Ad.created_at, Index.city_id, Index.region_id).join(Index, Index.ad_id == Ad.id).all()
    print(f"Ads with an index row: {len(rows)}")

    plan = []
    for ad_id, location, created_at, city_id, region_id in rows:
        new_city, new_region = resolve_ad_location(db, location)
        if (new_city, new_region) != (city_id, region_id):
            plan.append({
                "id": ad_id, "location": location, "created_at": created_at.isoformat() if created_at else None,
                "old_city_id": city_id, "old_region_id": region_id, "new_city_id": new_city, "new_region_id": new_region,
            })

    def label(city_id, region_id):
        return f"{cities.get(city_id, '-')}, {regions.get(region_id, '-')}"

    print(f"Index rows to correct: {len(plan)}")
    wrong = collections.Counter(label(row["old_city_id"], row["old_region_id"]) for row in plan)
    print("Index areas that lose the most ads:")
    for name, count in wrong.most_common(15):
        print(f"  {count:5}  {name}")
    kinds = collections.Counter(
        "area removed (the ad names none)" if row["old_region_id"] and not row["new_region_id"] else
        "area added" if not row["old_region_id"] and row["new_region_id"] else
        "area changed" if row["old_region_id"] != row["new_region_id"] else "city only"
        for row in plan
    )
    print("Kind of change:", dict(kinds))
    newest = max((row["created_at"] or "" for row in plan), default="")
    print("Newest ad that needs correcting was created:", newest)
    return plan


def _in_batches(db, rows, city_key, region_key):
    import models

    done = 0
    rows = sorted(rows, key=lambda row: row["id"])
    for start in range(0, len(rows), BATCH):
        chunk = {row["id"]: row for row in rows[start:start + BATCH]}
        for attempt in range(1, RETRIES + 1):
            try:
                for index in db.query(models.AdSearchIndex).filter(models.AdSearchIndex.ad_id.in_(list(chunk))).all():
                    index.city_id, index.region_id = chunk[index.ad_id][city_key], chunk[index.ad_id][region_key]
                db.commit()
                done += len(chunk)
                break
            except Exception as error:
                db.rollback()
                if attempt == RETRIES:
                    raise
                print(f"  batch at {start} failed ({type(error).__name__}), retry {attempt}")
                time.sleep(2 * attempt)
    return done


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    parser.add_argument("--rollback", metavar="BACKUP_JSON", help="put back the values saved by an earlier --apply")
    args = parser.parse_args()

    sys.path.append("/app")
    from database import SessionLocal

    db = SessionLocal()
    try:
        if args.rollback:
            rows = json.load(open(args.rollback, encoding="utf-8"))
            print(f"Restored {_in_batches(db, rows, 'old_city_id', 'old_region_id')} index rows.")
            return
        plan = build_plan(db)
        if not args.apply:
            print("Dry run: nothing was changed. Run again with --apply.")
            return
        db.rollback()
        name = f"index_location_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(name, "w", encoding="utf-8") as handle:
            json.dump(plan, handle, ensure_ascii=False)
        print(f"Backup of the old values: {name}")
        print(f"Corrected {_in_batches(db, plan, 'new_city_id', 'new_region_id')} index rows.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

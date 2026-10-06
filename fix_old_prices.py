"""
Applies the scraper's price checks (price_guard.py) to the scraped ads already in
the database.

For every scraped real-estate ad that has a price:

  * a sale filed under rentals (or a rental under sales) moves to the matching
    category on the right side;
  * a price that is a size, a per-metre price, an instalment, or outside what a
    rent or a sale can be, is removed. The ad stays, with no price, and the old
    value is kept in its attributes under "refused_price".

Old ads are treated more gently than new ones in one respect: a price that is
simply not found in the text is only removed when it is also very low (a rent
under 80, a sale under 5,000). Higher ones are mostly real prices written in a way
the check cannot read ("17لف") or totals worked out from a price per dunum.

Run from the backend folder:

    python fix_old_prices.py                 # dry run: prints the plan, writes price_fix_plan.csv
    python fix_old_prices.py --apply         # writes price_fix_backup_<time>.json, then updates
    python fix_old_prices.py --rollback price_fix_backup_<time>.json

Ads posted by people in the app are never touched.
"""
import argparse
import collections
import csv
import json
import sys
import time

from price_guard import category_for_deal, check_price, corrected_deal, deal_of_category

NOT_WRITTEN = "the price is not written in the post"
# Below these a price missing from the text is a slip, not an unusual spelling
LOW_PRICE = {"rent": 80, "sale": 5_000}
DEAL_TYPE = {"rent": "RENT", "sale": "SALE"}
BATCH = 200
RETRIES = 5


def build_plan(db):
    import models

    parents = dict(db.query(models.Category.id, models.Category.parent_id).all())
    names = dict(db.query(models.Category.id, models.Category.name).all())
    Ad = models.Ad
    ads = db.query(Ad.id, Ad.category_id, Ad.price, Ad.title, Ad.raw_description, Ad.description).filter(
        Ad.source_type != models.SourceType.ORGANIC_USER, Ad.price > 0
    ).all()
    print(f"Scraped ads with a price: {len(ads)}")

    plan = []
    for ad_id, category_id, price, title, raw, description in ads:
        deal = deal_of_category(category_id, parents)
        if deal is None:
            continue
        price = float(price)
        text = str(raw or description or title or "")
        new_deal = corrected_deal(price, deal, text)
        new_category = category_for_deal(category_id, new_deal, parents) if new_deal != deal else category_id
        new_price, reason = check_price(price, new_deal, text)
        if reason == NOT_WRITTEN and price >= LOW_PRICE[new_deal]:
            new_price, reason = price, "ok"
        if new_category == category_id and new_price == price:
            continue
        plan.append({
            "id": ad_id, "old_price": price, "new_price": new_price, "old_category_id": category_id,
            "new_category_id": new_category, "old_category": names.get(category_id, ""),
            "new_category": names.get(new_category, ""), "new_deal": new_deal,
            "reason": "moved to " + new_deal if new_price == price else reason, "title": (title or "")[:80],
        })
    return plan


def print_summary(plan):
    removed = [row for row in plan if row["new_price"] != row["old_price"]]
    moved = [row for row in plan if row["new_category_id"] != row["old_category_id"]]
    print(f"\nAds to change: {len(plan)}")
    print(f"  prices removed: {len(removed)}")
    for reason, count in collections.Counter(row["reason"].split(" for a ")[0].split("outside")[0] or "outside the plausible range" for row in removed).most_common():
        print(f"    {count:5}  {reason}")
    print(f"  moved between rent and sale: {len(moved)}")
    for (old, new), count in collections.Counter((row["old_category"], row["new_category"]) for row in moved).most_common(15):
        print(f"    {count:5}  {old}  ->  {new}")


def _in_batches(db, ids, change):
    """Small transactions, each retried on its own: the site is live and one long
    transaction over thousands of ads deadlocks with its writes."""
    import models

    ids = sorted(ids)
    done = 0
    for start in range(0, len(ids), BATCH):
        chunk = ids[start:start + BATCH]
        for attempt in range(1, RETRIES + 1):
            try:
                index = {i.ad_id: i for i in db.query(models.AdSearchIndex).filter(models.AdSearchIndex.ad_id.in_(chunk)).all()}
                ads = db.query(models.Ad).filter(models.Ad.id.in_(chunk)).order_by(models.Ad.id).all()
                for ad in ads:
                    change(ad, index.get(ad.id))
                db.commit()
                done += len(ads)
                break
            except Exception as error:
                db.rollback()
                if attempt == RETRIES:
                    raise
                print(f"  batch at {start} failed ({type(error).__name__}), retry {attempt}")
                time.sleep(2 * attempt)
    return done


def apply_plan(db, plan):
    import models
    from sqlalchemy.orm.attributes import flag_modified

    by_id = {row["id"]: row for row in plan}
    ids = sorted(by_id)

    backup = []
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        index = {i.ad_id: i for i in db.query(models.AdSearchIndex).filter(models.AdSearchIndex.ad_id.in_(chunk)).all()}
        for ad in db.query(models.Ad).filter(models.Ad.id.in_(chunk)).all():
            idx = index.get(ad.id)
            backup.append({
                "id": ad.id, "price": float(ad.price) if ad.price is not None else None, "category_id": ad.category_id,
                "index_price": float(idx.price) if idx and idx.price is not None else None,
                "index_category_id": idx.category_id if idx else None, "index_deal_type": idx.deal_type if idx else None,
            })
    db.rollback()
    name = f"price_fix_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(name, "w", encoding="utf-8") as handle:
        json.dump(backup, handle, ensure_ascii=False)
    print(f"Backup of the old values: {name}")

    def change(ad, idx):
        row = by_id[ad.id]
        if row["new_price"] != row["old_price"]:
            ad.price = row["new_price"]
            ad.attributes = {**(ad.attributes if isinstance(ad.attributes, dict) else {}), "refused_price": f"{row['old_price']:g}: {row['reason']}"}
            flag_modified(ad, "attributes")
            if idx:
                idx.price = row["new_price"]
        if row["new_category_id"] != row["old_category_id"]:
            ad.category_id = row["new_category_id"]
            if idx:
                idx.category_id = row["new_category_id"]
                idx.deal_type = DEAL_TYPE[row["new_deal"]]

    print(f"Changed {_in_batches(db, ids, change)} ads.")


def rollback(db, path):
    from sqlalchemy.orm.attributes import flag_modified

    rows = json.load(open(path, encoding="utf-8"))
    by_id = {row["id"]: row for row in rows}

    def change(ad, idx):
        row = by_id[ad.id]
        ad.price, ad.category_id = row["price"], row["category_id"]
        if isinstance(ad.attributes, dict) and "refused_price" in ad.attributes:
            ad.attributes = {key: value for key, value in ad.attributes.items() if key != "refused_price"}
            flag_modified(ad, "attributes")
        if idx:
            idx.price, idx.category_id, idx.deal_type = row["index_price"], row["index_category_id"], row["index_deal_type"]

    print(f"Restored {_in_batches(db, list(by_id), change)} ads from {path}.")


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
            rollback(db, args.rollback)
            return
        plan = build_plan(db)
        print_summary(plan)
        fields = ["id", "old_price", "new_price", "old_category", "new_category", "reason", "title"]
        with open("price_fix_plan.csv", "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(plan)
        print("\nFull plan: price_fix_plan.csv")
        if args.apply:
            apply_plan(db, plan)
        else:
            print("Dry run: nothing was changed. Run again with --apply to change the ads.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

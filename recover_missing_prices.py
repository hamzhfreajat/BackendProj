"""
Reads the price out of scraped ads that have none stored, when the post itself
states exactly one clearly labelled price ("السعر 65 الف", "الاجرة 350 دينار").

The reader (price_guard.extract_price) is strict on purpose: it gives no answer
for ranges, discounts, per-metre prices, instalments, posts with a second amount
that could be the price, or a bare number with no label. Measured on 21,291 ads
whose stored price is trusted, it answered for about half of them and agreed with
the stored price 99.7% of the time for rentals and 99.96% for sales (and most of
the disagreements were the stored price being wrong, not the reader).

Run from the backend folder:

    python recover_missing_prices.py                 # dry run: prints the plan, writes price_recovery_plan.csv
    python recover_missing_prices.py --apply         # writes price_recovery_backup_<time>.json, then updates
    python recover_missing_prices.py --rollback price_recovery_backup_<time>.json

Ads posted by people in the app are never touched. Each recovered ad is marked in
its attributes with "recovered_price", so it can always be told apart.
"""
import argparse
import collections
import csv
import json
import sys
import time

from fix_old_prices import _in_batches
from price_guard import deal_of_category, extract_price


def build_plan(db):
    import models
    from sqlalchemy import func

    parents = dict(db.query(models.Category.id, models.Category.parent_id).all())
    Ad = models.Ad
    ads = db.query(Ad.id, Ad.category_id, Ad.title, Ad.raw_description, Ad.attributes).filter(
        Ad.source_type != models.SourceType.ORGANIC_USER, func.coalesce(Ad.price, 0) <= 0, Ad.raw_description.isnot(None)
    ).all()
    print(f"Scraped ads with no price: {len(ads)}")

    plan, reasons = [], collections.Counter()
    for ad_id, category_id, title, raw, attributes in ads:
        deal = deal_of_category(category_id, parents)
        if deal is None:
            reasons["not real estate"] += 1
            continue
        # A price that the checks removed earlier is not put back by another route
        if isinstance(attributes, dict) and attributes.get("refused_price"):
            reasons["price was refused earlier"] += 1
            continue
        price, why = extract_price(raw, deal)
        reasons[why] += 1
        if price:
            plan.append({"id": ad_id, "price": price, "deal": deal, "title": (title or "")[:80], "text": " ".join(str(raw).split())[:300]})
    print("Outcome per ad:")
    for why, count in reasons.most_common():
        print(f"  {count:6}  {why}")
    return plan


def apply_plan(db, plan):
    from sqlalchemy.orm.attributes import flag_modified

    by_id = {row["id"]: row for row in plan}
    name = f"price_recovery_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(name, "w", encoding="utf-8") as handle:
        json.dump([{"id": row["id"], "price": row["price"]} for row in plan], handle)
    print(f"List of the ads changed: {name}")

    def change(ad, idx):
        row = by_id[ad.id]
        # Only an ad that still has no price: someone may have edited it since the plan was made
        if ad.price and float(ad.price) > 0:
            return
        ad.price = row["price"]
        ad.attributes = {**(ad.attributes if isinstance(ad.attributes, dict) else {}), "recovered_price": True}
        flag_modified(ad, "attributes")
        if idx:
            idx.price = row["price"]

    print(f"Processed {_in_batches(db, list(by_id), change)} ads.")


def rollback(db, path):
    from sqlalchemy.orm.attributes import flag_modified

    by_id = {row["id"]: row for row in json.load(open(path, encoding="utf-8"))}

    def change(ad, idx):
        # Only undo what this script set
        if not (isinstance(ad.attributes, dict) and ad.attributes.get("recovered_price")):
            return
        ad.price = 0
        ad.attributes = {key: value for key, value in ad.attributes.items() if key != "recovered_price"}
        flag_modified(ad, "attributes")
        if idx:
            idx.price = 0

    print(f"Processed {_in_batches(db, list(by_id), change)} ads from {path}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    parser.add_argument("--rollback", metavar="BACKUP_JSON", help="remove the prices set by an earlier --apply")
    args = parser.parse_args()

    sys.path.append("/app")
    from database import SessionLocal

    db = SessionLocal()
    try:
        if args.rollback:
            rollback(db, args.rollback)
            return
        plan = build_plan(db)
        by_deal = collections.Counter(row["deal"] for row in plan)
        print(f"\nPrices to set: {len(plan)}  (rent {by_deal['rent']}, sale {by_deal['sale']})")
        with open("price_recovery_plan.csv", "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "deal", "price", "title", "text"])
            writer.writeheader()
            writer.writerows(plan)
        print("Full plan: price_recovery_plan.csv")
        if args.apply:
            apply_plan(db, plan)
        else:
            print("Dry run: nothing was changed. Run again with --apply to set the prices.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

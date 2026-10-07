"""
Files scraped ads whose stored location is not a city and area the site knows.

Two kinds are handled:

  * an area written another way ("عمان, جبيهة" for "عمان, الجبيهة", "إربد, الرهبات الوردية"
    for "إربد, الراهبات"): the stored words themselves say which area is meant, so the
    ad is given that area's exact name;
  * no place at all ("غير محدد"): the ad is filed only where its own text names the place,
    read with the same rules as relocate_misfiled_ads.py (whole words, no short or everyday
    names without a sign they are a place, no "طريق عمان" or "شرق جرش").

Anything the text does not settle is left exactly as it is.

    python place_unfiled_ads.py                 # dry run: prints the plan, writes unfiled_plan.csv
    python place_unfiled_ads.py --apply         # writes relocation_backup_<time>.json, then updates
    python place_unfiled_ads.py --rollback relocation_backup_<time>.json

Ads posted by people in the app are never touched: they chose their location.
"""
import argparse
import collections
import csv
import sys

from relocate_misfiled_ads import DIRECTIONS, NO_REGION, ROAD_WORDS, Places, ad_text, apply_plan, fold, print_summary, rollback


# A name of two words or more this long is not mistaken for ordinary words
LONG_NAME = 8
NEAR_WORDS = DIRECTIONS | {"قرب", "بقرب", "بالقرب", "قريب", "قريبه", "مقابل", "مقابيل", "خلف", "بجانب", "جانب", "جنب", "امام", "عند", "من", "عن", "حول", "قبل", "بعد", "علي", "طريق", "باتجاه", "نحو"}
# The governorate Salt is in, listed as one of its areas: naming it says nothing about the area
NOT_AN_AREA = {"البلقاء"}


def same_area(places: Places, city_id, words: str):
    """The area of this city that the stored words name in another spelling, if exactly one does."""
    key = fold(words)
    bare = key[2:] if key.startswith("ال") else key
    matches = set()
    for (region_city, name), region_id in places.region_by_name.items():
        if region_city == city_id and (name[2:] if name.startswith("ال") else name) == bare:
            matches.add(region_id)
    for kind, ident in places.targets.get(key, []):  # the inner part of "شارع الجامعة (اليرموك)", or an alias
        if kind == "region" and places.region[ident][0] == city_id:
            matches.add(ident)
    return next(iter(matches)) if len(matches) == 1 else None


# How far apart a city and a one-word area may be to count as written together ("السلط - زي", "مادبا في ماعين")
TOGETHER = 4


def from_text(places: Places, text: str):
    """(city_id, region_id, reason) for an ad with no stored place, or None when the text does not settle it.

    The text has to name one city and only one. An area is taken only with its own city beside it:
    on their own, one-word names are too often something else ("تذاكر العودة", "مطبخ من العالمية",
    "مسجد علياء التل").
    """
    found = places.find(text)
    folded = fold(text)
    cities = []
    for kind, ident, pos, phrase in found:
        # "طريق اوتوستراد اربد عمان": a city one or two words after a road word is where the road goes
        if kind == "city" and not any(word in ROAD_WORDS for word in folded[:pos].split()[-2:]):
            cities.append((ident, pos, phrase))
    if len({ident for ident, _, _ in cities}) != 1:
        return None
    city_id = cities[0][0]

    def beside_city(pos, phrase):
        return any(0 <= pos - (c_pos + len(c_phrase)) <= TOGETHER or 0 <= c_pos - (pos + len(phrase)) <= TOGETHER for _, c_pos, c_phrase in cities)

    accepted = []
    for kind, ident, pos, phrase in found:
        if kind != "region" or places.region[ident][0] != city_id:
            continue
        # "مقابل الهابي لاند", "شرق شارع الحصن": the ad is near that place, not in it
        if phrase in NOT_AN_AREA or (folded[:pos].split()[-1:] or [""])[0] in NEAR_WORDS:
            continue
        if beside_city(pos, phrase) or (" " in phrase and not places.risky(phrase) and len(phrase.replace(" ", "")) >= LONG_NAME):
            accepted.append((pos, -len(phrase), ident))
    areas = {ident for _, _, ident in accepted}
    if len(areas) == 1:
        region_id = accepted[0][2]
        return city_id, region_id, f"the text names {places.region[region_id][1]}"
    # No area, or several: the city alone is certain
    return city_id, None, "the text names the city"


def build_plan(db):
    import models

    cities = [(c.id, c.name_ar) for c in db.query(models.City).all()]
    regions = [(r.id, r.city_id, r.name_ar) for r in db.query(models.Region).all()]
    aliases = [(a.region_id, a.alias_name) for a in db.query(models.RegionAlias).all()]
    places = Places(cities, regions, aliases)
    known = {f"{places.city_name[city_id]}, {name}" for city_id, name in places.region.values()} | set(places.city_name.values())

    Ad = models.Ad
    ads = db.query(Ad).filter(Ad.source_type != models.SourceType.ORGANIC_USER, Ad.location.isnot(None)).all()
    print(f"Scraped ads read: {len(ads)}")

    plan, left = [], collections.Counter()
    for ad in ads:
        location = (ad.location or "").strip()
        if not location or location in known:
            continue
        parts = [p.strip() for p in location.replace("،", ",").split(",", 1)]
        city_id = places.city_by_key.get(fold(parts[0]))
        words = parts[1] if len(parts) > 1 else ""

        result = None
        if city_id is not None and words:
            if fold(words) in NO_REGION or fold(words) == fold(parts[0]):
                continue  # "عمان, مناطق أخرى", "جرش, جرش": the city is right and no area is claimed
            region_id = same_area(places, city_id, words)
            if region_id is not None:
                result = (city_id, region_id, "another spelling of this area")
            # An unknown area in a known city stays as it is: guessing a neighbour from the
            # text is how "مجمع عمان" ads ended up in the wrong place
        elif city_id is None:
            result = from_text(places, ad_text(ad))
        if result is None:
            left[location] += 1
            continue
        new_city, new_region, reason = result
        new_location = places.location_text(new_city, new_region)
        if new_location == location:
            continue
        plan.append({
            "id": ad.id, "old_location": location, "new_location": new_location, "new_city_id": new_city,
            "new_region_id": new_region, "reason": reason, "title": (ad.title or "")[:80],
            "live": bool(ad.is_published and not ad.is_rejected),
        })
    print(f"Left as they are (the text settles nothing): {sum(left.values())}")
    for location, count in left.most_common(12):
        print(f"  {count:5}  {location}")
    return places, plan


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="write the changes (default is a dry run)")
    parser.add_argument("--rollback", metavar="BACKUP_JSON", help="put back the values saved by an earlier --apply")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    from database import SessionLocal

    db = SessionLocal()
    try:
        if args.rollback:
            rollback(db, args.rollback)
            return
        _, plan = build_plan(db)
        print_summary(plan)
        print(f"\nOf these, live on the site: {sum(row['live'] for row in plan)}")
        print("By reason:", dict(collections.Counter(row["reason"].split(" names ")[0] for row in plan)))
        with open("unfiled_plan.csv", "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "old_location", "new_location", "reason", "live", "title"], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(plan)
        if args.apply:
            apply_plan(db, plan)
        else:
            print("\nDry run. Nothing was changed; the plan is in unfiled_plan.csv.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

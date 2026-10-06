"""
Finds scraped ads that sit under an area their own text never mentions, and moves
them to the area the text does name.

Why they exist: the search index used to guess an ad's area from the first place
name anywhere in its text, matched as a *part* of an area name ("بادر بالاتصال" ->
"الكرك, أدر", "فرصة نادرة" -> "المفرق, نادرة", plain "اربد" -> "مستشفى اربد التخصصي").
fix_ad_locations_sql.py then copied those guesses over every ad's location.

Run inside the backend container:

    python relocate_misfiled_ads.py                 # dry run: prints the plan, writes relocation_plan.csv
    python relocate_misfiled_ads.py --apply         # writes relocation_backup_<time>.json, then updates
    python relocate_misfiled_ads.py --rollback relocation_backup_<time>.json

Ads posted by people in the app are never touched: they chose their location.
"""
import argparse
import collections
import csv
import json
import re
import sys
import time

# ---------------------------------------------------------------------------
# Reading place names out of ad text (no database needed, so it can be tested)
# ---------------------------------------------------------------------------
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
NO_REGION = {"", "اخري", "مناطق اخري", "other", "غير محدد"}
# A word before a short or everyday name that shows it is meant as a place
MARKERS = {"في", "ب", "منطقه", "بمنطقه", "موقع", "الموقع", "حي", "بحي", "قريه", "بلده", "لواء", "اراضي", "حوض", "ضاحيه", "جبل"}
DIRECTIONS = {"شرق", "غرب", "شمال", "جنوب", "الشرقي", "الغربي", "الشمالي", "الجنوبي"}
# A city name after one of these is a road or a landmark, not where the ad is ("طريق عمان", "مجمع عمان")
ROAD_WORDS = ["طريق", "شارع", "باب", "مجمع", "جسر", "اوتوستراد", "اتوستراد", "خط", "دوار", "مثلث", "اشاره", "كراج", "كراجات", "موقف", "باصات"]
# Area names that are also everyday words in ads; they only count next to a marker or a city
EVERYDAY = {"نادره", "الزهور", "النزهه", "الروضه", "السلام", "النور", "الرشيد", "الامل", "المنار", "الربيع", "الفردوس",
            "النخيل", "الجامعه", "المدينه", "الحديقه", "المطار", "الاستقلال", "الحريه", "النهضه", "الوسط", "المركز",
            "السوق", "البلد", "الاسكان", "المنطقه", "الحي", "الجبل", "الوادي", "الدوار", "المحطه", "الصناعيه"}
# Names this short are parts of ordinary words ("أدر" in "بادر", "لب" in "طلب")
SHORT_NAME = 3
# A joined-on "ب" or "ل" is only read as "in" / "to" before a name longer than this
PREFIXED_NAME = 4
# A city after one of these is a point of reference ("شرق جرش", "تبعد عن عمان"), not where the ad is
REFERENCE_WORDS = DIRECTIONS | {"عن", "من", "الي", "باتجاه", "نحو", "قبل", "بعد", "علي"}
# Names this long are also found glued to the word before them ("خلفيطبربور")
GLUED_NAME = 6
UNKNOWN_LOCATION = "غير محدد"
LATER = 10 ** 6


def fold(value) -> str:
    """One spelling for every variant, with punctuation and hashtags turned into spaces."""
    text = str(value or "").translate(_ARABIC_DIGITS)
    text = re.sub("[أإآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")
    text = re.sub("[ً-ْـ]", "", text)  # diacritics and the stretching mark ("للايجــار")
    text = re.sub(r"[^0-9A-Za-zء-ي]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def name_variants(name: str):
    """"شارع الجامعة (الجامعة الأردنية)" is found by either part."""
    outer = re.sub(r"\(.*?\)", " ", name)
    inner = re.findall(r"\((.*?)\)", name)
    return [v for v in dict.fromkeys(fold(part) for part in [outer, *inner]) if v]


class Places:
    """Every city and area, ready to be looked for in text."""

    def __init__(self, cities, regions, aliases=()):
        """cities: [(id, name)], regions: [(id, city_id, name)], aliases: [(region_id, alias)]"""
        self.city_name = {c_id: name for c_id, name in cities}
        self.city_by_key = {fold(name): c_id for c_id, name in cities}
        self.region = {r_id: (city_id, name) for r_id, city_id, name in regions}
        self.region_by_name = {(city_id, fold(name)): r_id for r_id, city_id, name in regions}
        # What "no particular area" is called in each city ("أخرى" or "مناطق أخرى")
        self.other_name = {}
        for r_id, city_id, name in regions:
            if fold(name) in NO_REGION and (city_id not in self.other_name or fold(name) == "اخري"):
                self.other_name[city_id] = name

        self.targets = collections.defaultdict(list)  # folded phrase -> [("region", id) | ("city", id) | ("road", None)]
        for r_id, city_id, name in regions:
            if fold(name) in NO_REGION or fold(name) in self.city_by_key:
                continue
            for variant in name_variants(name):
                self.targets[variant].append(("region", r_id))
        for region_id, alias in aliases:
            if region_id in self.region and fold(alias):
                self.targets[fold(alias)].append(("region", region_id))
        for key, c_id in self.city_by_key.items():
            self.targets[key].append(("city", c_id))
            for road in ROAD_WORDS:
                self.targets[f"{road} {key}"].append(("road", None))
        phrases = sorted(self.targets, key=len, reverse=True)
        self.pattern = re.compile(r"(?<![0-9A-Za-zء-ي])([وبلف]?)(" + "|".join(re.escape(p) for p in phrases) + r")(?![0-9A-Za-zء-ي])")
        glued = [p for p in phrases if self.targets[p][0][0] == "region" and len(p.replace(" ", "")) >= GLUED_NAME and p not in EVERYDAY]
        self.glued_pattern = re.compile("(" + "|".join(re.escape(p) for p in glued) + r")(?![0-9A-Za-zء-ي])") if glued else None

    def risky(self, phrase: str) -> bool:
        return len(phrase.replace(" ", "")) <= SHORT_NAME or phrase in EVERYDAY

    def find(self, text: str):
        """Places named in the text: (kind, id, position, phrase)."""
        folded = fold(text)
        found = []
        for match in self.pattern.finditer(folded):
            prefix, phrase = match.group(1), match.group(2)
            kinds = self.targets[phrase]
            if kinds[0][0] == "road":
                continue
            is_city = any(kind == "city" for kind, _ in kinds)
            if is_city and (folded[: match.start()].split()[-1:] or [""])[0] in REFERENCE_WORDS:
                continue
            if not is_city and self.risky(phrase):
                # "بادر" is not "ب + أدر": short and everyday names need a real sign they are a place
                if prefix:
                    continue
                before = folded[: match.start()].split()[-1:] or [""]
                after = folded[match.end():].split()[:1] or [""]
                near_city = before[0] in self.city_by_key or after[0] in self.city_by_key
                if not (before[0] in MARKERS or near_city or after[0] in DIRECTIONS):
                    continue
            elif prefix and len(phrase.replace(" ", "")) <= PREFIXED_NAME:
                continue
            # "تبعد 1 كم عن شارع الأردن" measures a distance: such an area ranks after every other one
            measured = not is_city and (folded[: match.start()].split()[-1:] or [""])[0] == "عن"
            for kind, ident in kinds:
                found.append((kind, ident, match.start() + (LATER if measured else 0), phrase))
        if self.glued_pattern and not any(kind == "region" for kind, _, _, _ in found):
            for match in self.glued_pattern.finditer(folded):
                for kind, ident in self.targets[match.group(1)]:
                    found.append((kind, ident, match.start(), match.group(1)))
        return found

    def location_text(self, city_id, region_id=None) -> str:
        if city_id is None:
            return UNKNOWN_LOCATION
        city = self.city_name[city_id]
        if region_id is not None:
            return f"{city}, {self.region[region_id][1]}"
        return f"{city}, {self.other_name[city_id]}" if city_id in self.other_name else city

    def parse_location(self, location: str):
        """(city_id, region_id) of a stored "المدينة, المنطقة"; unknown parts are None."""
        parts = [p.strip() for p in str(location or "").replace("،", ",").split(",", 1)]
        city_id = self.city_by_key.get(fold(parts[0])) if parts and parts[0] else None
        if city_id is None or len(parts) < 2 or fold(parts[1]) in NO_REGION:
            return city_id, None
        return city_id, self.region_by_name.get((city_id, fold(parts[1])))


def is_trap(places: Places, region_id) -> bool:
    """Areas the old guessing fell into: short or everyday names, and names that hold a city's name."""
    name = places.region[region_id][1]
    variants = name_variants(name)
    if any(places.risky(v) for v in variants):
        return True
    words = set(" ".join(variants).split())
    return any(city in words for city in places.city_by_key)


def judge(places: Places, text: str, location: str, group_city=None, title: str = ""):
    """What to do with one ad: (action, new_city_id, new_region_id, reason).

    action is "keep" (the text supports the stored area, or there is nothing better),
    or "move".
    """
    city_id, region_id = places.parse_location(location)
    found = places.find(text)
    regions = [(ident, pos, phrase) for kind, ident, pos, phrase in found if kind == "region"]
    cities = [ident for kind, ident, _, _ in found if kind == "city"]

    if region_id is None:
        return "keep", city_id, None, "no area stored"
    # The title counts as support for the stored area, never as a reason to move: scraped
    # titles are written by the AI and now and then name a place the post never mentioned
    titled = [(ident, pos, phrase) for kind, ident, pos, phrase in places.find(title) if kind == "region"] if title else []
    if any(ident == region_id for ident, _, _ in regions + titled):
        return "keep", city_id, region_id, "the text names this area"

    # "تلاع العلي" in the text supports "تلاع العلي الشمالي": the stored area is the finer one
    stored = name_variants(places.region[region_id][1])
    if any(places.region[ident][0] == city_id and any(phrase in variant for variant in stored) for ident, _, phrase in regions + titled):
        return "keep", city_id, region_id, "the text names the wider area"

    # The stored area is not in the text. Which area is?
    def pick(pool):
        # The first area named is where the ad is; later ones are usually what it is near
        return sorted(pool, key=lambda item: (item[1], -len(item[2])))[0][0]

    by_city = collections.defaultdict(list)
    for item in regions:
        by_city[places.region[item[0]][0]].append(item)

    chosen = None
    # Only the first city named is taken as the ad's own; later ones are usually views and distances
    for candidate_city in [*cities[:1], group_city]:
        if candidate_city in by_city:
            chosen = pick(by_city[candidate_city])
            break
    if chosen is None and len(by_city) == 1 and not cities:
        chosen = pick(next(iter(by_city.values())))
    if chosen is not None:
        return "move", places.region[chosen][0], chosen, f"the text names {places.region[chosen][1]}"

    if not is_trap(places, region_id):
        # No better area and no sign of a bad guess: it was probably matched by a landmark
        return "keep", city_id, region_id, "no other area in the text"

    # A trap area the text does not support: keep only the city the text or the ad's group points to.
    # With neither, the honest answer is "unknown" rather than a village in Karak.
    new_city = cities[0] if cities else group_city
    if new_city is None:
        return "move", None, None, "the text names no place"
    return "move", new_city, None, "the text names no area"


# ---------------------------------------------------------------------------
# Database part
# ---------------------------------------------------------------------------
GROUP_RE = re.compile(r"groups/(\d+)")
MIN_GROUP_ADS = 8
MIN_GROUP_SHARE = 0.8


def ad_text(ad) -> str:
    """The advertiser's own words (the title only when there is nothing else)."""
    return str(ad.raw_description or ad.description or ad.title or "")


def build_plan(db):
    sys.path.append("/app")
    import models

    cities = [(c.id, c.name_ar) for c in db.query(models.City).all()]
    regions = [(r.id, r.city_id, r.name_ar) for r in db.query(models.Region).all()]
    aliases = [(a.region_id, a.alias_name) for a in db.query(models.RegionAlias).all()]
    places = Places(cities, regions, aliases)

    Ad = models.Ad
    ads = db.query(Ad).filter(Ad.source_type != models.SourceType.ORGANIC_USER, Ad.location.isnot(None)).all()
    print(f"Scraped ads read: {len(ads)}")

    # Which city each Facebook group belongs to, judged by the ads whose area the text supports
    votes = collections.defaultdict(collections.Counter)
    first = {}
    for ad in ads:
        first[ad.id] = judge(places, ad_text(ad), ad.location, None, ad.title or "")
        group = GROUP_RE.search(ad.source_url or "")
        if group and first[ad.id][3] == "the text names this area":
            votes[group.group(1)][first[ad.id][1]] += 1
    group_city = {}
    for group, counter in votes.items():
        city, count = counter.most_common(1)[0]
        if sum(counter.values()) >= MIN_GROUP_ADS and count / sum(counter.values()) >= MIN_GROUP_SHARE:
            group_city[group] = city

    plan = []
    for ad in ads:
        group = GROUP_RE.search(ad.source_url or "")
        hint = group_city.get(group.group(1)) if group else None
        action, new_city, new_region, reason = judge(places, ad_text(ad), ad.location, hint, ad.title or "") if hint else first[ad.id]
        if action != "move":
            continue
        new_location = places.location_text(new_city, new_region)
        if fold(new_location) == fold(ad.location):
            continue
        plan.append({
            "id": ad.id, "old_location": ad.location, "new_location": new_location, "new_city_id": new_city,
            "new_region_id": new_region, "reason": reason, "title": (ad.title or "")[:80],
        })
    return places, plan


def print_summary(plan):
    moves = collections.Counter((row["old_location"], row["new_location"]) for row in plan)
    leaving = collections.Counter(row["old_location"] for row in plan)
    print(f"\nAds to move: {len(plan)}")
    print("\nMost emptied locations:")
    for location, count in leaving.most_common(25):
        print(f"  {count:5}  {location}")
    print("\nMost common moves:")
    for (old, new), count in moves.most_common(40):
        print(f"  {count:5}  {old}  ->  {new}")


BATCH = 200
RETRIES = 5


def _in_batches(db, ids, change):
    """Runs `change(ad, index_row)` over the ads in small transactions. The site is live, so
    one long transaction over thousands of ads deadlocks with its own writes; a small
    one that fails is simply tried again."""
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
            except Exception as error:  # deadlock or lock timeout: undo this batch and retry it
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

    # The old values are saved to a file before anything is changed
    backup = []
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        index = {i.ad_id: i for i in db.query(models.AdSearchIndex).filter(models.AdSearchIndex.ad_id.in_(chunk)).all()}
        for ad in db.query(models.Ad).filter(models.Ad.id.in_(chunk)).all():
            idx = index.get(ad.id)
            attributes = ad.attributes if isinstance(ad.attributes, dict) else {}
            backup.append({
                "id": ad.id, "location": ad.location, "attr_city": attributes.get("city"), "attr_region": attributes.get("region"),
                "city_id": idx.city_id if idx else None, "region_id": idx.region_id if idx else None,
            })
    db.rollback()
    name = f"relocation_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(name, "w", encoding="utf-8") as handle:
        json.dump(backup, handle, ensure_ascii=False)
    print(f"Backup of the old values: {name}")

    def change(ad, idx):
        row = by_id[ad.id]
        ad.location = row["new_location"]
        attributes = ad.attributes if isinstance(ad.attributes, dict) else None
        if attributes is not None and ("city" in attributes or "region" in attributes):
            city, _, region = row["new_location"].partition(", ")
            ad.attributes = {**attributes, "city": city, "region": region or None}
            flag_modified(ad, "attributes")
        if idx:
            idx.city_id, idx.region_id = row["new_city_id"], row["new_region_id"]

    print(f"Moved {_in_batches(db, ids, change)} ads.")


def rollback(db, path):
    from sqlalchemy.orm.attributes import flag_modified

    rows = json.load(open(path, encoding="utf-8"))
    by_id = {row["id"]: row for row in rows}

    def change(ad, idx):
        row = by_id[ad.id]
        ad.location = row["location"]
        if isinstance(ad.attributes, dict) and ("city" in ad.attributes or "region" in ad.attributes):
            ad.attributes = {**ad.attributes, "city": row["attr_city"], "region": row["attr_region"]}
            flag_modified(ad, "attributes")
        if idx:
            idx.city_id, idx.region_id = row["city_id"], row["region_id"]

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
        _, plan = build_plan(db)
        print_summary(plan)
        with open("relocation_plan.csv", "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "old_location", "new_location", "reason", "title"], extrasaction="ignore")
            writer.writeheader()
            writer.writerows(plan)
        print("\nFull plan: relocation_plan.csv")
        if args.apply:
            apply_plan(db, plan)
        else:
            print("Dry run: nothing was changed. Run again with --apply to move the ads.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
The last check on a scraped ad's location before it is saved.

An ad is only ever stored under a city and area that exist in the cities and regions tables,
written exactly as they are there. Anything else ("عمان, جبيهة", an area the AI made up, no
place at all) is settled here, with the rules of place_unfiled_ads.py:

  * another spelling of a known area becomes that area's own name;
  * an area the tables do not have is dropped and the city is kept;
  * with no city, the ad is filed only where its own text names one city, and an area only
    when it is written beside that city. Otherwise it stays "غير محدد".
"""
import logging
import re
import time

from place_unfiled_ads import NEAR_WORDS, from_text, same_area
from relocate_misfiled_ads import NO_REGION, UNKNOWN_LOCATION, Places, fold

logger = logging.getLogger(__name__)

_CACHE_SECONDS = 600
_cache = {"places": None, "at": 0.0}


def _places(db) -> Places:
    if _cache["places"] is None or time.time() - _cache["at"] > _CACHE_SECONDS:
        import models

        cities = [(c.id, c.name_ar) for c in db.query(models.City).all()]
        regions = [(r.id, r.city_id, r.name_ar) for r in db.query(models.Region).all()]
        aliases = [(a.region_id, a.alias_name) for a in db.query(models.RegionAlias).all()]
        _cache["places"], _cache["at"] = Places(cities, regions, aliases), time.time()
    return _cache["places"]


# A city after one of these is a landmark's name or a view, not where the ad is ("جامعة عمان الأهلية")
NOT_ITS_CITY = NEAR_WORDS | {"جامعه", "مستشفي", "بنك", "مطله", "مطل", "اطلاله", "تطل", "مجمع", "كليه", "بلديه", "امانه"}
# A city after one of these is the ad's address ("الموقع: إربد، شارع القدس")
STATED = {"الموقع", "موقع", "موقعها", "موقعه", "العنوان", "في", "مدينه", "بمدينه", "محافظه"}


def stated_elsewhere(places: Places, city_id, text: str):
    """(city_id, region_id) when the ad's own words plainly put it in another city than `city_id`, else None.

    Ads were filed under عمان while their text ended with "الموقع: الزرقاء، شارع الجيش". The other
    city wins only when the text never mentions the stored one, names no area of it, names exactly
    one city, and states it as an address. Hashtags are reach, not an address.
    """
    text = re.sub(r"#\S+", " ", text or "")
    folded = fold(text)
    stored = fold(places.city_name[city_id])
    if not folded or stored in folded:
        return None
    found = places.find(text)
    if any(kind == "region" and places.region[ident][0] == city_id and not places.risky(phrase) for kind, ident, _, phrase in found):
        return None
    if any(kind == "city" and (folded[:pos].split()[-1:] or [""])[0] in NOT_ITS_CITY for kind, _, pos, _ in found):
        return None
    named = from_text(places, text)
    if named is None or named[0] == city_id:
        return None
    city = fold(places.city_name[named[0]])
    area = fold(places.region[named[1]][1]) if named[1] is not None else None
    words = folded.split()
    for index, word in enumerate(words):
        if word != city and not (word[:1] in "بل" and word[1:] == city):
            continue
        around = " ".join(words[max(0, index - 4): index + 6])
        if index == 0 or word != city or words[index - 1] in STATED or (area and area in around):
            return named[0], named[1]
    return None


def settle(places: Places, location: str, text: str = "", ai_location: str = "") -> str:
    """The location to store, given what the import arrived at, the post's text and the AI's own answer."""
    location = (location or "").strip()
    parts = [p.strip() for p in location.replace("،", ",").split(",", 1)]
    city_id = places.city_by_key.get(fold(parts[0])) if parts[0] else None
    words = parts[1] if len(parts) > 1 else ""

    if city_id is not None:
        elsewhere = stated_elsewhere(places, city_id, text)
        if elsewhere is not None:
            return places.location_text(*elsewhere)
        if not words or fold(words) == fold(parts[0]):
            return places.location_text(city_id)
        if fold(words) in NO_REGION:
            return places.location_text(city_id)
        region_id = places.region_by_name.get((city_id, fold(words)))
        if region_id is None:
            region_id = same_area(places, city_id, words)
        return places.location_text(city_id, region_id) if region_id is not None else places.location_text(city_id)

    # No city. The AI sometimes answers with the area alone ("طبربور"): good when only one city has it
    bare = fold(ai_location or "")
    if bare and "," not in (ai_location or "") and not places.risky(bare):
        matches = {ident for kind, ident in places.targets.get(bare, []) if kind == "region"}
        if len(matches) == 1 and not any(kind == "city" for kind, _ in places.targets.get(bare, [])):
            region_id = next(iter(matches))
            return places.location_text(places.region[region_id][0], region_id)
    named = from_text(places, text or "")
    if named is not None:
        return places.location_text(named[0], named[1])
    return UNKNOWN_LOCATION


def settle_location(db, location: str, text: str = "", ai_location: str = "") -> str:
    """`settle` against the live tables. Never raises: on any failure the location is returned unchanged."""
    try:
        settled = settle(_places(db), location, text, ai_location)
        if settled != (location or "").strip():
            logger.info(f"Location '{location}' stored as '{settled}'")
        return settled
    except Exception as error:
        logger.error(f"Could not settle location '{location}': {error}")
        return location

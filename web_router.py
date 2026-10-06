"""
Read-only API for the public website (sooq-com.com).

The website renders pages on the server for search engines, so these endpoints
return exactly what one page needs in one call: the ads, how many there are,
price statistics and the links to neighbouring pages.

Only "web quality" ads are exposed here: live, with a price, at least one photo
and a real description. Thin ads (mostly incomplete scraped posts) stay in the
app but are kept away from search engines.
"""
import json
import re
import time
from types import SimpleNamespace
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

import models
from database import get_db
from image_processing import card_url

router = APIRouter(prefix="/api/web", tags=["web"])

REAL_ESTATE_ROOTS = {"rent": 3, "sale": 2}
MIN_DESCRIPTION_LENGTH = 60
MAX_PAGE_SIZE = 48

# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------
_PHONE_RE = re.compile(r"(?:\+?962|00962|0)\s?7[\s\-]?[789](?:[\s\-]?\d){7}")
_DIGIT_RUN_RE = re.compile(r"\d{7,}")
# Emoji, pictographs, dingbats, variation selectors and decorative symbols
_SYMBOL_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002190-\U000023FF\U00002460-\U000027BF\U00002900-\U00002BFF"
    "\U0000FE00-\U0000FE0F\U0000200B-\U0000200F\U00002066-\U00002069\U000E0020-\U000E007F]+"
)
_NOISE_PREFIX_RE = re.compile(r"^(?:للاستفسار|للتواصل|اتصال|واتساب|هاتف|جوال)\s*[:\-]?\s*", re.IGNORECASE)
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def clean_text(value: Optional[str]) -> str:
    """Removes emoji, phone numbers and decoration, and collapses whitespace."""
    if not value:
        return ""
    value = value.translate(_ARABIC_DIGITS)
    value = _SYMBOL_RE.sub(" ", value)
    value = _PHONE_RE.sub(" ", value)
    value = _DIGIT_RUN_RE.sub(" ", value)
    value = re.sub(r"[|•●▪■□◆◇★☆*_=~#]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" -–—:،,.")
    previous = None
    while previous != value:
        previous = value
        value = _NOISE_PREFIX_RE.sub("", value).strip(" -–—:،,.")
    return value


def web_title(title: Optional[str], category_name: str, region_name: Optional[str], city_name: Optional[str]) -> str:
    """A title fit for a search result. Falls back to one built from the ad's data
    when the original is empty, too short or just contact details."""
    cleaned = clean_text((title or "").split("\n")[0])
    if len(cleaned) < 12 or not re.search(r"[؀-ۿA-Za-z]{3,}", cleaned):
        place = "، ".join([p for p in (region_name, city_name) if p])
        cleaned = f"{category_name} في {place}" if place else category_name
    return cleaned[:110]


def _fold(value: str) -> str:
    """Folds Arabic spelling variants so "الجبيهه" matches "الجبيهة"."""
    return re.sub("[أإآ]", "ا", value).replace("ة", "ه").replace("ى", "ي")


SEO_TITLE_LENGTH = 70


def seo_title(title: str, deal: Optional[str], region_name: Optional[str], city_name: Optional[str]) -> str:
    """The title a search engine shows for an ad. Most ad titles leave out whether it is
    for rent or sale and where it is, which are the words people search with, so they
    are added when missing and when they fit."""
    folded = _fold(title)
    result = title
    deal_word = {"rent": "للإيجار", "sale": "للبيع"}.get(deal or "")
    mentions_deal = any(word in folded for word in ("للايجار", "ايجار", "اجار", "للبيع", "بيع"))
    if deal_word and not mentions_deal and len(result) + len(deal_word) + 1 <= SEO_TITLE_LENGTH:
        result = f"{result} {deal_word}"
    missing = [p for p in (region_name, city_name) if p and p != "أخرى" and _fold(p) not in folded]
    while missing:
        place = "، ".join(missing)
        if len(result) + len(place) + 4 <= SEO_TITLE_LENGTH:
            result = f"{result}، {place}" if " في " in result else f"{result} في {place}"
            break
        # The area matters more than the city, so the city is dropped first
        missing.pop()
    return result


def slugify(value: str) -> str:
    """URL slug that keeps Arabic letters: spaces and punctuation become dashes."""
    value = clean_text(value).lower()
    # Drop diacritics and the elongation mark, then turn everything that is not a
    # letter or digit (including Arabic punctuation) into a dash
    value = re.sub(r"[ً-ٰٟـ]", "", value)
    value = re.sub(r"[^0-9a-zء-غف-ي]+", "-", value)
    return value.strip("-")[:80]


def _images(ad) -> List[str]:
    urls: List[str] = []
    attributes = ad.attributes if isinstance(ad.attributes, dict) else {}
    listed = attributes.get("image_urls")
    if isinstance(listed, list):
        urls.extend(str(u) for u in listed if u)
    raw = (ad.image_url or "").strip()
    if raw.startswith("["):
        try:
            urls.extend(str(u) for u in json.loads(raw) if u)
        except ValueError:
            pass
    elif raw:
        urls.append(raw)
    return list(dict.fromkeys(u for u in urls if u.startswith("http")))


# ---------------------------------------------------------------------------
# Taxonomy (cached in memory: it changes rarely and every page needs it)
# ---------------------------------------------------------------------------
_taxonomy_cache = {"at": 0.0, "data": None}
TAXONOMY_TTL_SECONDS = 600


def _taxonomy(db: Session) -> dict:
    if _taxonomy_cache["data"] is not None and time.time() - _taxonomy_cache["at"] < TAXONOMY_TTL_SECONDS:
        return _taxonomy_cache["data"]

    rows = db.query(models.Category.id, models.Category.parent_id, models.Category.name).all()
    children: Dict[Optional[int], List[int]] = {}
    for c_id, parent_id, _ in rows:
        children.setdefault(parent_id, []).append(c_id)
    names = {c_id: name for c_id, _, name in rows}
    parents = {c_id: parent_id for c_id, parent_id, _ in rows}

    def descendants(root: int) -> List[int]:
        found, stack = [], [root]
        while stack:
            current = stack.pop()
            found.append(current)
            stack.extend(children.get(current, []))
        return found

    real_estate_ids = set(descendants(REAL_ESTATE_ROOTS["rent"]) + descendants(REAL_ESTATE_ROOTS["sale"]))
    cities = db.query(models.City).order_by(models.City.id).all()
    regions = db.query(models.Region).all()

    data = {
        "children": children,
        "names": names,
        "parents": parents,
        "descendants": descendants,
        "real_estate_ids": real_estate_ids,
        # Plain copies: database objects stop working once their session is closed
        "cities": {c.id: SimpleNamespace(id=c.id, name_ar=c.name_ar, name_en=c.name_en) for c in cities},
        "regions": {
            r.id: SimpleNamespace(id=r.id, city_id=r.city_id, name_ar=r.name_ar, name_en=r.name_en,
                                  latitude=r.latitude, longitude=r.longitude)
            for r in regions
        },
    }
    _taxonomy_cache.update(at=time.time(), data=data)
    return data


def _deal_of(category_id: Optional[int], tax: dict) -> Optional[str]:
    current = category_id
    seen = set()
    while current is not None and current not in seen:
        seen.add(current)
        if current == REAL_ESTATE_ROOTS["rent"]:
            return "rent"
        if current == REAL_ESTATE_ROOTS["sale"]:
            return "sale"
        current = tax["parents"].get(current)
    return None


def _breadcrumb(category_id: Optional[int], tax: dict) -> List[dict]:
    chain, current, seen = [], category_id, set()
    while current is not None and current not in seen:
        seen.add(current)
        chain.append({"id": current, "name": tax["names"].get(current, "")})
        current = tax["parents"].get(current)
    return list(reversed(chain))


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------
# Prices outside these ranges are not prices of the property: a rent of 5 is a slip of the
# extraction, a "rent" of 65,000 is a sale filed under rentals, a sale at 200 is a monthly
# instalment or a price per metre, and one at 90,000,000 is an ad in another country's currency.
# Such ads stay in the app but are kept off the website, where they would also distort the
# price statistics shown on every page. (Daily lets start around 10; yearly rents reach 30,000.)
PLAUSIBLE_PRICE = {"rent": (10, 30_000), "sale": (1_500, 15_000_000)}


def _plausible_price(tax: dict):
    Index = models.AdSearchIndex
    checks = []
    for deal, (low, high) in PLAUSIBLE_PRICE.items():
        ids = tax["descendants"](REAL_ESTATE_ROOTS[deal])
        checks.append(and_(Index.category_id.in_(ids), Index.price >= low, Index.price <= high))
    return or_(*checks)


def _quality_query(db: Session):
    """Live ads good enough to show on the web, joined to their search-index row."""
    Ad, Index = models.Ad, models.AdSearchIndex
    return db.query(Ad, Index).join(Index, Index.ad_id == Ad.id).filter(
        _plausible_price(_taxonomy(db)),
        Ad.is_published == True,
        func.coalesce(Ad.is_paused, False) == False,
        func.coalesce(Ad.is_sold, False) == False,
        func.coalesce(Ad.is_rejected, False) == False,
        Index.price > 0,
        Ad.image_url.isnot(None),
        Ad.image_url.notin_(["", "[]"]),
        func.length(func.coalesce(Ad.description, "")) >= MIN_DESCRIPTION_LENGTH,
    )


# The card swipes through the first few; the full-screen viewer opened from the card shows them all
CARD_IMAGES = 12
EXCERPT_LENGTH = 180


def _detail(ad, key: str):
    attributes = ad.attributes if isinstance(ad.attributes, dict) else {}
    dynamic = attributes.get("dynamic_data") if isinstance(attributes.get("dynamic_data"), dict) else {}
    value = dynamic.get(key)
    return value if value not in (None, "", []) else None


# ---------------------------------------------------------------------------
# Attribute filters ("facets"): the same refinements the app offers. They live
# in the ad's free-form attributes, mostly under "dynamic_data".
#   one  - the ad holds a single value; several chosen values mean "any of them"
#   many - the ad holds a list; every chosen value has to be present
# ---------------------------------------------------------------------------
FACETS = {
    "floor": ("one", [("dynamic_data", "floor"), ("floor",)]),
    "age": ("one", [("dynamic_data", "building_age"), ("dynamic_data", "age"), ("building_age",)]),
    "rent_duration": ("one", [("dynamic_data", "rent_duration"), ("rent_duration",)]),
    "furnished": ("one", [("dynamic_data", "furnished"), ("dynamic_data", "furnishing"), ("furnished",)]),
    "facade": ("one", [("dynamic_data", "facade")]),
    "payment_method": ("one", [("payment_method",), ("dynamic_data", "payment_method")]),
    "land_type": ("one", [("dynamic_data", "land_type")]),
    "zoning_classification": ("one", [("dynamic_data", "zoning_classification")]),
    "geometric_shape": ("one", [("dynamic_data", "geometric_shape")]),
    "topography": ("one", [("dynamic_data", "topography")]),
    "ownership_type": ("one", [("dynamic_data", "ownership_type")]),
    "is_mortgaged": ("one", [("dynamic_data", "is_mortgaged")]),
    "installment_possible": ("one", [("dynamic_data", "installment_possible")]),
    "main_features": ("many", [("dynamic_data", "key_features"), ("dynamic_data", "main_features"), ("key_features",)]),
    "extra_features": ("many", [("dynamic_data", "building_features"), ("dynamic_data", "extra_features"), ("building_features",)]),
    "nearby": ("many", [("dynamic_data", "nearby_places"), ("dynamic_data", "nearby"), ("nearby_places",)]),
    "available_services": ("many", [("dynamic_data", "available_services")]),
}
# Other spellings of the same value found in the data
FACET_ALIASES = {
    "الطابق الأرضي": ["طابق أرضي", "طابق الأرضي", "أرضي"],
    "1": ["الطابق الأول"], "2": ["الطابق الثاني"], "3": ["الطابق الثالث"], "4": ["الطابق الرابع"],
    "10 - 19 سنوات": ["10 - 19 سنة"],
    "+20 سنة": ["20+ سنة"],
    "كل أربع أشهر": ["كل 4 أشهر", "كل 4 شهور"],
    "غير مفروشة": ["غير مفروش", "فارغة"],
    "مفروشة": ["مفروش"],
    "مفروش جزئياً": ["مفروشة جزئياً"],
    "ملك": ["مُلك", "طابو"],
}
# For list values a distinctive part of the wording is searched, so "يوجد مصعد" also finds "مصعد"
FACET_NEEDLES = {
    "يوجد مصعد": "مصعد", "شرفة / بلكونة": "بلكون", "حارس / أمن وحماية": "حارس", "تكييف مركزي": "تكييف",
    "صالة رياضية / جيم": "رياضي", "بنك / صراف آلي": "بنك", "مدرسة": "مدرس", "شوارع معبدة": "معبد",
    "إنترنت": "نترنت", "مسبح خاص": "مسبح", "بركة سباحة": "سباح", "نظام كهرباء احتياطي للطوارئ": "احتياطي",
}
MAX_FACET_VALUES = 40


def _attr(path):
    column = models.Ad.attributes
    for key in path:
        column = column[key]
    return column.astext


def _like(value: str) -> str:
    return "%" + value.replace("%", "").replace("_", " ") + "%"


def _apply_facets(query, selections: Optional[List[str]]):
    """`selections` are "name:value" strings, e.g. "floor:2" or "main_features:كراج"."""
    grouped: Dict[str, List[str]] = {}
    for item in (selections or [])[:MAX_FACET_VALUES]:
        name, _, value = item.partition(":")
        value = value.strip()[:60]
        if name in FACETS and value:
            grouped.setdefault(name, []).append(value)
    for name, values in grouped.items():
        kind, paths = FACETS[name]
        if kind == "one":
            accepted = []
            for value in values:
                accepted.append(value)
                accepted.extend(FACET_ALIASES.get(value, []))
            query = query.filter(or_(*[_attr(path).in_(accepted) for path in paths]))
        else:
            for value in values:
                needle = _like(FACET_NEEDLES.get(value, value))
                query = query.filter(or_(*[_attr(path).ilike(needle) for path in paths]))
    return query


def _int_list(value: Optional[str], limit: int = 12) -> List[int]:
    return [int(part) for part in (value or "").split(",") if part.strip().isdigit()][:limit]


def _as_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,،]", value) if part.strip()]
    return []


_EMPTY_TAGS = {"غير محدد", "غير مذكورة", "لم يُذكر", "أخرى", "لا", "False", "True", "0"}
CARD_TAGS = 8


def _card_tags(ad) -> List[str]:
    """Short labels shown on the card, in the order the app shows them."""
    attributes = ad.attributes if isinstance(ad.attributes, dict) else {}
    dynamic = attributes.get("dynamic_data") if isinstance(attributes.get("dynamic_data"), dict) else {}

    def one(*keys):
        for key in keys:
            value = dynamic.get(key) if dynamic.get(key) not in (None, "", []) else attributes.get(key)
            if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value).strip():
                return str(value).strip()
        return None

    tags: List[str] = []
    for value in (
        one("rent_duration"),
        one("furnished", "furnishing"),
        one("land_type"),
        one("zoning_classification"),
        one("payment_method"),
        one("building_age", "age"),
    ):
        if value:
            tags.append(value)
    if one("installment_possible") == "نعم":
        tags.append("أقساط")
    tags.extend(_as_list(dynamic.get("key_features") or attributes.get("key_features") or dynamic.get("main_features"))[:4])
    tags.extend(_as_list(dynamic.get("building_features") or attributes.get("building_features") or dynamic.get("extra_features"))[:3])
    tags.extend(_as_list(dynamic.get("available_services"))[:3])
    cleaned: List[str] = []
    for tag in tags:
        tag = clean_text(tag)
        if tag and tag not in _EMPTY_TAGS and len(tag) <= 28 and tag not in cleaned:
            cleaned.append(tag)
    return cleaned[:CARD_TAGS]


def _card(ad, index, tax: dict) -> dict:
    city = tax["cities"].get(index.city_id)
    region = tax["regions"].get(index.region_id)
    category_name = tax["names"].get(ad.category_id, "عقار")
    images = _images(ad)
    title = web_title(ad.title, category_name, region.name_ar if region else None, city.name_ar if city else None)
    deal = _deal_of(ad.category_id, tax)
    return {
        "id": ad.id,
        "title": title,
        "seo_title": seo_title(title, deal, region.name_ar if region else None, city.name_ar if city else None),
        "slug": slugify(title),
        "price": float(index.price) if index.price is not None else None,
        "deal": deal,
        "category_id": ad.category_id,
        "category_name": category_name,
        "city_id": index.city_id,
        "region_id": index.region_id,
        "city_ar": city.name_ar if city else None,
        "city_en": city.name_en if city else None,
        "region_ar": region.name_ar if region else None,
        "region_en": region.name_en if region else None,
        "image": card_url(images[0]) if images else None,
        # Card-size photos, so the card can be swiped and enlarged without opening the ad
        "images": [card_url(u) for u in images[:CARD_IMAGES]],
        "images_count": len(images),
        "excerpt": clean_text(ad.description)[:EXCERPT_LENGTH],
        "floor": _detail(ad, "floor"),
        "tags": _card_tags(ad),
        "is_hot": bool(getattr(ad, "is_hot", False)),
        "is_featured": bool(getattr(ad, "is_featured", False)),
        "below_market": getattr(ad, "market_price_status", None) == "BELOW_MARKET",
        "has_video": isinstance(ad.attributes, dict) and bool(ad.attributes.get("video_url")),
        "phone": getattr(ad, "phone_number", None) or None,
        "is_organic": str(getattr(ad.source_type, "value", ad.source_type) or "") == "ORGANIC_USER",
        "bedrooms": index.bedrooms,
        "bathrooms": index.bathrooms,
        "area": float(index.build_area) if index.build_area is not None else None,
        "furnished": index.furnished,
        "rating_avg": float(ad.rating_avg) if getattr(ad, "rating_avg", None) is not None else None,
        "reviews_count": getattr(ad, "reviews_count", 0) or 0,
        "created_at": ad.created_at.isoformat() if ad.created_at else None,
    }


def _apply_scope(query, tax: dict, category_id: Optional[int], city_id: Optional[int], region_id: Optional[int]):
    Index = models.AdSearchIndex
    if category_id is not None:
        query = query.filter(Index.category_id.in_(tax["descendants"](category_id)))
    else:
        query = query.filter(Index.category_id.in_(tax["real_estate_ids"]))
    if city_id is not None:
        query = query.filter(Index.city_id == city_id)
    if region_id is not None:
        query = query.filter(Index.region_id == region_id)
    return query


# Rental ads mix monthly and yearly prices. Above this amount a rent is almost
# always a yearly figure, so it is divided by 12 before computing statistics.
YEARLY_RENT_THRESHOLD = 1500


def _comparable_price(deal: Optional[str]):
    """The price column to compare ads by. Rentals are compared per month, so an ad
    priced per year (6,000) lines up with one priced per month (500)."""
    Index = models.AdSearchIndex
    if deal == "rent":
        return case((Index.price >= YEARLY_RENT_THRESHOLD, Index.price / 12), else_=Index.price)
    return Index.price


def _price_stats(query, deal: Optional[str] = None) -> dict:
    """Median and typical range (10th-90th percentile). For rentals the figures are monthly."""
    Index = models.AdSearchIndex
    price = _comparable_price(deal)
    row = query.with_entities(
        func.count(Index.ad_id),
        func.percentile_cont(0.5).within_group(price),
        func.percentile_cont(0.1).within_group(price),
        func.percentile_cont(0.9).within_group(price),
    ).order_by(None).first()
    count, median, low, high = row
    if not count:
        return {"count": 0, "median": None, "low": None, "high": None}
    return {"count": count, "median": round(float(median)), "low": round(float(low)), "high": round(float(high))}


# Rent periods that have a page of their own on the website ("شقق للإيجار اليومي")
RENT_PERIODS = {"daily": "يومي", "monthly": "شهري"}


def _rent_period():
    """"daily", "monthly" or NULL, read from the ad's free-form attributes."""
    stored = func.coalesce(_attr(("dynamic_data", "rent_duration")), _attr(("rent_duration",)))
    return case(*[(stored == value, key) for key, value in RENT_PERIODS.items()], else_=None)


# ---------------------------------------------------------------------------
# Refinements read from the ad itself: no agent, payable in instalments, ground floor
# ---------------------------------------------------------------------------
PRICE_CAPS = {"rent": [150, 200, 250, 300], "sale": [20000, 30000, 40000, 50000]}
_GROUND_FLOOR = ["الطابق الأرضي", "طابق أرضي", "طابق الأرضي", "أرضي"]


def _ad_text():
    return func.coalesce(models.Ad.raw_description, models.Ad.description, "")


def _by_owner():
    """The advertiser says there is no agent, and nothing in the ad says otherwise."""
    text = _ad_text()
    return and_(
        text.op("~")("من المالك|المالك مباش|بدون وسيط|بدون وسطاء|بدون سمسار"),
        text.op("!~")("مكتب عقار|مكاتب عقار|للعقارات|العقاري[ةه]|عمول[ةه]|وسيط عقاري|شركة عقار"),
    )


def _instalments():
    return or_(
        _attr(("dynamic_data", "installment_possible")) == "نعم",
        _attr(("dynamic_data", "payment_method")).in_(["أقساط", "كاش أو أقساط"]),
        _attr(("payment_method",)).in_(["أقساط", "كاش أو أقساط"]),
        _ad_text().op("~")("تقسيط|[اأ]قساط"),
    )


def _ground_floor():
    return or_(_attr(("dynamic_data", "floor")).in_(_GROUND_FLOOR), _attr(("floor",)).in_(_GROUND_FLOOR))


def _feature_conditions(deal: Optional[str]) -> dict:
    """Every refinement that applies to the deal, as {name: condition}. Ceilings are "cap:200"."""
    Index = models.AdSearchIndex
    conditions = {"owner": _by_owner(), "ground": _ground_floor()}
    if deal == "rent":
        conditions["unfurnished"] = Index.furnished == False
    if deal == "sale":
        conditions["instalments"] = _instalments()
    price = _comparable_price(deal)
    for cap in PRICE_CAPS.get(deal or "", []):
        conditions[f"cap:{cap}"] = price <= cap
    return conditions


def _refinement_counts(scope, deal: Optional[str]) -> dict:
    """How many ads of the page's scope each narrower page would hold, so the page
    can link to them (and only to the ones that are not empty)."""
    Ad, Index = models.Ad, models.AdSearchIndex
    bedrooms = dict(
        scope.with_entities(Index.bedrooms, func.count(Ad.id)).filter(Index.bedrooms.between(1, 6))
        .group_by(Index.bedrooms).order_by(None).all()
    )
    counts = {"bedrooms": [{"value": n, "count": bedrooms[n]} for n in sorted(bedrooms)], "furnished": 0, "daily": 0, "monthly": 0}
    if deal == "rent":
        period = _rent_period()
        counts["furnished"] = scope.filter(Index.furnished == True).with_entities(func.count(Ad.id)).order_by(None).scalar() or 0
        by_period = dict(scope.with_entities(period, func.count(Ad.id)).group_by(period).order_by(None).all())
        counts["daily"] = by_period.get("daily", 0)
        counts["monthly"] = by_period.get("monthly", 0)
    # One pass over the ads for all of the rest
    conditions = _feature_conditions(deal) if deal else {}
    if conditions:
        names = list(conditions)
        row = scope.with_entities(*[func.count(Ad.id).filter(conditions[name]) for name in names]).order_by(None).first()
        counts["caps"] = {}
        for name, value in zip(names, row):
            if name.startswith("cap:"):
                counts["caps"][name[4:]] = value or 0
            else:
                counts[name] = value or 0
    return counts


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/taxonomy")
def get_taxonomy(db: Session = Depends(get_db)):
    """Real-estate categories, cities and regions: everything needed to build URLs."""
    tax = _taxonomy(db)
    categories = [
        {"id": c_id, "parent_id": tax["parents"].get(c_id), "name": tax["names"].get(c_id, "")}
        for c_id in sorted(tax["real_estate_ids"])
    ]
    cities = [{"id": c.id, "name_ar": c.name_ar, "name_en": c.name_en} for c in tax["cities"].values()]
    regions = [
        {
            "id": r.id, "city_id": r.city_id, "name_ar": r.name_ar, "name_en": r.name_en,
            "lat": float(r.latitude) if r.latitude is not None else None,
            "lng": float(r.longitude) if r.longitude is not None else None,
        }
        for r in tax["regions"].values()
    ]
    return {"categories": categories, "cities": cities, "regions": regions}


@router.get("/landing")
def get_landing(
    category_id: Optional[int] = None,
    city_id: Optional[int] = None,
    region_id: Optional[int] = None,
    region_ids: Optional[str] = Query(None, description="Comma-separated region ids (several regions at once)"),
    bedrooms: Optional[str] = Query(None, description="One or several, comma-separated. 0 is a studio, 6 means 6 or more"),
    bathrooms: Optional[str] = Query(None, description="One or several, comma-separated. 6 means 6 or more"),
    furnished: Optional[bool] = None,
    owner: Optional[bool] = Query(None, description="Only ads placed by the owner, with no agent"),
    instalments: Optional[bool] = Query(None, description="Only ads that can be paid in instalments"),
    attrs: Optional[List[str]] = Query(None, description='Attribute filters as "name:value", repeatable'),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_area: Optional[float] = Query(None, ge=0),
    max_area: Optional[float] = Query(None, ge=0),
    sort: str = Query("newest", pattern="^(newest|price_asc|price_desc)$"),
    page: int = Query(1, ge=1, le=500),
    page_size: int = Query(24, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    """One listing page: ads, total, price statistics and links to narrower pages."""
    tax = _taxonomy(db)
    Ad, Index = models.Ad, models.AdSearchIndex
    if category_id is not None and category_id not in tax["real_estate_ids"]:
        raise HTTPException(status_code=404, detail="Unknown category")
    if city_id is not None and city_id not in tax["cities"]:
        raise HTTPException(status_code=404, detail="Unknown city")
    if region_id is not None:
        region = tax["regions"].get(region_id)
        if region is None or (city_id is not None and region.city_id != city_id):
            raise HTTPException(status_code=404, detail="Unknown region")

    scope = _apply_scope(_quality_query(db), tax, category_id, city_id, region_id)
    wanted_regions = _int_list(region_ids, 50) if region_id is None else []
    if wanted_regions:
        scope = scope.filter(Index.region_id.in_(wanted_regions))

    filtered = scope
    wanted_beds = _int_list(bedrooms)
    if wanted_beds:
        # 6 means "6 or more", matching the filter's last option
        filtered = filtered.filter(or_(*[Index.bedrooms >= 6 if n >= 6 else Index.bedrooms == n for n in wanted_beds]))
    wanted_baths = _int_list(bathrooms)
    if wanted_baths:
        filtered = filtered.filter(or_(*[Index.bathrooms >= 6 if n >= 6 else Index.bathrooms == n for n in wanted_baths]))
    filtered = _apply_facets(filtered, attrs)
    if min_area is not None:
        filtered = filtered.filter(Index.build_area >= min_area)
    if max_area is not None:
        filtered = filtered.filter(Index.build_area <= max_area)
    if furnished is not None:
        filtered = filtered.filter(Index.furnished == furnished)
    if owner:
        filtered = filtered.filter(_by_owner())
    if instalments:
        filtered = filtered.filter(_instalments())
    price = _comparable_price(_deal_of(category_id, tax) if category_id is not None else None)
    if min_price is not None:
        filtered = filtered.filter(price >= min_price)
    if max_price is not None:
        filtered = filtered.filter(price <= max_price)

    total = filtered.with_entities(func.count(Ad.id)).scalar() or 0
    order = {
        "newest": Ad.created_at.desc(),
        "price_asc": price.asc(),
        "price_desc": price.desc(),
    }[sort]
    rows = filtered.order_by(order, Ad.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # Links to narrower pages, counted on the unfiltered scope
    locations = []
    if region_id is None:
        column = Index.region_id if city_id is not None else Index.city_id
        counts = scope.with_entities(column, func.count(Ad.id)).filter(column.isnot(None)).group_by(column).order_by(
            func.count(Ad.id).desc()
        ).limit(60).all()
        source = tax["regions"] if city_id is not None else tax["cities"]
        for loc_id, count in counts:
            place = source.get(loc_id)
            if place is not None:
                locations.append({"id": loc_id, "name_ar": place.name_ar, "name_en": place.name_en, "count": count})

    # How many ads each category of this deal has in the chosen place (children included),
    # so the category picker can show every level with counts and leave out empty branches
    category_counts = []
    deal = _deal_of(category_id, tax) if category_id is not None else None
    if deal:
        root = REAL_ESTATE_ROOTS[deal]
        place_scope = _apply_scope(_quality_query(db), tax, root, city_id, region_id)
        if wanted_regions:
            place_scope = place_scope.filter(Index.region_id.in_(wanted_regions))
        raw = dict(place_scope.with_entities(Index.category_id, func.count(Ad.id)).group_by(Index.category_id).all())
        for c_id in tax["descendants"](root):
            count = sum(raw.get(d, 0) for d in tax["descendants"](c_id))
            if count:
                category_counts.append({"id": c_id, "count": count})
    # The categories one level down, taken from the same counts instead of another query
    by_id = {entry["id"]: entry["count"] for entry in category_counts}
    child_categories = sorted(
        (
            {"id": child_id, "name": tax["names"].get(child_id, ""), "count": by_id[child_id]}
            for child_id in tax["children"].get(category_id, [])
            if child_id in by_id
        ),
        key=lambda c: -c["count"],
    )

    refinements = _refinement_counts(scope, deal)

    return {
        "category_counts": category_counts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "ads": [_card(ad, index, tax) for ad, index in rows],
        # Mixing rent and sale prices would be meaningless, so stats need a category
        "stats": _price_stats(filtered, _deal_of(category_id, tax)) if category_id is not None else None,
        "deal": _deal_of(category_id, tax),
        "locations": locations,
        "bedrooms": refinements["bedrooms"],
        "refinements": {key: value for key, value in refinements.items() if key != "bedrooms"},
        "categories": child_categories,
        "breadcrumb": _breadcrumb(category_id, tax),
    }


@router.get("/ads/{ad_id}")
def get_web_ad(ad_id: int, db: Session = Depends(get_db)):
    """One ad page: the ad, its market context and similar ads."""
    tax = _taxonomy(db)
    Ad, Index = models.Ad, models.AdSearchIndex
    row = db.query(Ad, Index).join(Index, Index.ad_id == Ad.id).filter(Ad.id == ad_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Ad not found")
    ad, index = row
    if ad.category_id not in tax["real_estate_ids"]:
        raise HTTPException(status_code=404, detail="Ad not found")

    live = bool(ad.is_published) and not ad.is_paused and not ad.is_sold and not ad.is_rejected
    images = _images(ad)
    description = (ad.description or "").strip()
    low, high = PLAUSIBLE_PRICE.get(_deal_of(ad.category_id, tax) or "", (1, float("inf")))
    plausible = index.price is not None and low <= index.price <= high
    indexable = bool(live and plausible and images and len(description) >= MIN_DESCRIPTION_LENGTH)

    card = _card(ad, index, tax)
    attributes = ad.attributes if isinstance(ad.attributes, dict) else {}
    dynamic = attributes.get("dynamic_data") if isinstance(attributes.get("dynamic_data"), dict) else {}
    details = {
        key: dynamic.get(key)
        for key in ("floor", "building_age", "facade", "payment_method", "rent_duration", "main_features",
                    "extra_features", "nearby", "land_type", "zoning_classification")
        if dynamic.get(key) not in (None, "", [])
    }

    # Market context: comparable ads in the same category and place
    comparable = _apply_scope(_quality_query(db), tax, ad.category_id, index.city_id, index.region_id)
    if index.bedrooms is not None:
        narrowed = comparable.filter(Index.bedrooms == index.bedrooms)
        if (narrowed.with_entities(func.count(Ad.id)).scalar() or 0) >= 8:
            comparable = narrowed
    market = _price_stats(comparable, card["deal"])

    similar_rows = _apply_scope(_quality_query(db), tax, ad.category_id, index.city_id, index.region_id).filter(
        Ad.id != ad.id
    ).order_by(Ad.created_at.desc()).limit(8).all()
    if len(similar_rows) < 4 and index.city_id is not None:
        similar_rows = _apply_scope(_quality_query(db), tax, ad.category_id, index.city_id, None).filter(
            Ad.id != ad.id
        ).order_by(Ad.created_at.desc()).limit(8).all()

    # Scraped ads belong to a system account, which is not the advertiser
    is_organic = str(getattr(ad.source_type, "value", ad.source_type) or "") == "ORGANIC_USER"
    owner = ad.owner if is_organic else None
    return {
        **card,
        "image": images[0] if images else None,
        "images": images,
        "description": description,
        "live": live,
        "indexable": indexable,
        "updated_at": ad.updated_at.isoformat() if ad.updated_at else None,
        "location": ad.location,
        "details": details,
        "source_type": ad.source_type.value if hasattr(ad.source_type, "value") else str(ad.source_type or ""),
        "owner_name": (owner.full_name or owner.username) if owner is not None else None,
        "phone": (getattr(ad, "phone_number", None) or attributes.get("phone_number") or None) if live else None,
        "breadcrumb": _breadcrumb(ad.category_id, tax),
        "market": market,
        "similar": [_card(a, i, tax) for a, i in similar_rows],
    }


@router.get("/sitemap/landing")
def get_sitemap_landing(db: Session = Depends(get_db)):
    """Counts of web-quality ads per (category, city, region, bedrooms, furnished, rent
    period), so the website can list every landing page that has enough ads to be worth indexing."""
    tax = _taxonomy(db)
    Ad, Index = models.Ad, models.AdSearchIndex
    # Bedrooms outside 1-6 are grouped together so the result stays small
    bedrooms = case((Index.bedrooms.between(1, 6), Index.bedrooms), else_=None)
    furnished = func.coalesce(Index.furnished, False)
    period = _rent_period()
    rows = _quality_query(db).with_entities(
        Index.category_id, Index.city_id, Index.region_id, bedrooms, furnished, period,
        func.count(Ad.id), func.max(Ad.created_at)
    ).filter(Index.category_id.in_(tax["real_estate_ids"])).group_by(
        Index.category_id, Index.city_id, Index.region_id, bedrooms, furnished, period
    ).all()
    return [
        {
            "category_id": category_id, "city_id": city_id, "region_id": region_id, "bedrooms": beds,
            "furnished": bool(is_furnished), "rent_period": rent_period, "count": count,
            "latest": latest.isoformat() if latest else None,
        }
        for category_id, city_id, region_id, beds, is_furnished, rent_period, count, latest in rows
    ]


@router.get("/sitemap/features")
def get_sitemap_features(db: Session = Depends(get_db)):
    """Counts of web-quality ads per (refinement, category, city, region), for the pages
    "by owner", "unfurnished", "instalments", "ground floor" and the price ceilings."""
    tax = _taxonomy(db)
    Ad, Index = models.Ad, models.AdSearchIndex
    result = []
    for deal, root in REAL_ESTATE_ROOTS.items():
        base = _quality_query(db).filter(Index.category_id.in_(tax["descendants"](root)))
        for name, condition in _feature_conditions(deal).items():
            rows = base.filter(condition).with_entities(
                Index.category_id, Index.city_id, Index.region_id, func.count(Ad.id), func.max(Ad.created_at)
            ).group_by(Index.category_id, Index.city_id, Index.region_id).order_by(None).all()
            result.extend(
                {"feature": name, "category_id": category_id, "city_id": city_id, "region_id": region_id, "count": count,
                 "latest": latest.isoformat() if latest else None}
                for category_id, city_id, region_id, count, latest in rows
            )
    return result


@router.get("/sitemap/ads")
def get_sitemap_ads(
    page: int = Query(1, ge=1),
    page_size: int = Query(5000, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    """Web-quality ads for the ad sitemaps, newest first."""
    tax = _taxonomy(db)
    Ad, Index = models.Ad, models.AdSearchIndex
    base = _quality_query(db).filter(Index.category_id.in_(tax["real_estate_ids"]))
    total = base.with_entities(func.count(Ad.id)).scalar() or 0
    rows = base.order_by(Ad.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for ad, index in rows:
        city = tax["cities"].get(index.city_id)
        region = tax["regions"].get(index.region_id)
        title = web_title(ad.title, tax["names"].get(ad.category_id, "عقار"),
                          region.name_ar if region else None, city.name_ar if city else None)
        items.append({
            "id": ad.id,
            "slug": slugify(title),
            "updated_at": (ad.updated_at or ad.created_at).isoformat() if (ad.updated_at or ad.created_at) else None,
            # The main photo, for the image entry of the ad's sitemap line
            "image": next(iter(_images(ad)), None),
        })
    return {"total": total, "page": page, "page_size": page_size, "items": items}

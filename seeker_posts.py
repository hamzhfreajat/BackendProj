"""
Facebook posts from people LOOKING for a property ("مطلوب شقة للإيجار في طبربور").

The scraper throws these away because they are not ads. They are worth keeping, though:
each one is a person we can answer with a comment that links to matching ads on the site.
`detect` decides whether a post is such a request; `remember` stores it with its link.
"""
import re
from typing import Optional

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# How a request is worded. "المطلوب" (the asking price) is not one of these.
_SEEKING = [
    "مطلوب", "مطلوبه", "ابحث عن", "ابحث على", "ببحث عن", "نبحث عن", "بدور علي", "بدور عن", "بدور ع", "بدي", "بدنا", "محتاج", "محتاجه",
    "محتاجين", "لازمني", "لازمنا", "مين عنده", "مين عندو", "حدا عنده", "حدا عندو", "حد عنده", "في حدا عنده", "اريد", "ارغب",
]
# What is being looked for, and the property type it maps to
_PROPERTY = {
    "شقه": "apartment", "شقق": "apartment", "شقة": "apartment", "استوديو": "studio", "ستوديو": "studio", "بيت": "house", "منزل": "house",
    "دار": "house", "غرفه": "room", "غرفة": "room", "سكن": "housing", "فيلا": "villa", "فله": "villa", "روف": "roof", "ارض": "land",
    "قطعه ارض": "land", "محل": "shop", "مكتب": "office", "مخزن": "warehouse", "مستودع": "warehouse", "مزرعه": "farm", "شاليه": "chalet",
    "عماره": "building", "طابق": "floor",
}
# A request for a person or a service, not a property ("مطلوب موظفة", "مطلوب فني تكييف")
_NOT_PROPERTY = [
    "موظف", "موظفه", "موظفين", "موظفات", "عامل", "عامله", "عمال", "سائق", "سايق", "مندوب", "مندوبه", "محاسب", "سكرتير", "معلم", "معلمه",
    "فني", "صنايعي", "نجار", "سباك", "دهين", "بليط", "حداد", "كهربجي", "كهربائي", "خادمه", "شغاله", "مربيه", "طباخ", "شيف", "حارس",
    "مسوق", "مسوقه", "وسيط", "وسطاء", "شريك تجاري", "ممول", "مستثمر", "للعمل", "وظيفه", "وظائف", "راتب",
    # "بدي ابيع بيت" is an offer, not a request
    "ابيع", "نبيع", "اعرض", "نعرض", "ااجر", "اجر", "ناجر",
]
# Words that may sit between the request and the thing asked for ("مطلوب للإيجار فوراً شقة")
_GAP_WORDS = 6

_RENT = re.compile("ايجار|اجار|للاجار|استئجار|استاجر|مفروش|شهري|يومي|سنوي")
_SALE = re.compile("للشراء|شراء|اشتري|تمليك|للبيع|بيع|كاش|نقدا")


def _fold(text: str) -> str:
    """One spelling for the variants people type, with punctuation turned into spaces."""
    text = str(text or "").translate(_ARABIC_DIGITS)
    text = re.sub("[أإآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")
    text = re.sub("[ً-ْـ]", "", text)
    text = re.sub(r"[^0-9A-Za-zء-ي]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_SEEKING_FOLDED = sorted({_fold(word) for word in _SEEKING}, key=len, reverse=True)
_PROPERTY_FOLDED = {_fold(word): kind for word, kind in _PROPERTY.items()}
_NOT_PROPERTY_FOLDED = {_fold(word) for word in _NOT_PROPERTY}
_SEEKING_RE = re.compile(r"(?<![ء-ي])(" + "|".join(re.escape(word) for word in _SEEKING_FOLDED) + r")(?![ء-ي])")
_PROPERTY_RE = re.compile(r"(?<![ء-ي])(?:ال|لل|ل|ب)?(" + "|".join(re.escape(word) for word in sorted(_PROPERTY_FOLDED, key=len, reverse=True)) + r")(?![ء-ي])")


def detect(text: str) -> Optional[dict]:
    """`{"kind": "apartment", "deal": "rent"}` when the post asks for a property, else None.

    The request word has to be followed, within a few words, by a property word, with no word
    for a job or a trade in between. That keeps out "مطلوب موظفة", "مطلوب فني", and ads that
    merely state "المطلوب 40 ألف".
    """
    folded = _fold(text)
    if not folded:
        return None
    for match in _SEEKING_RE.finditer(folded):
        after = folded[match.end():].split()[: _GAP_WORDS + 1]
        if not after:
            continue
        # "مطلوب 250 دينار" is a price, and so is "مطلوب فيها 40 الف"
        if after[0].isdigit():
            continue
        window = " ".join(after)
        found = _PROPERTY_RE.search(window)
        if not found:
            continue
        before_property = window[: found.start()].split()
        if any(word in _NOT_PROPERTY_FOLDED or word.lstrip("ال") in _NOT_PROPERTY_FOLDED for word in before_property):
            continue
        # "مطلوب فيها 40 الف": a number before the property word means a price is being asked
        if any(word.isdigit() for word in before_property):
            continue
        kind = _PROPERTY_FOLDED[found.group(1)]
        deal = "rent" if _RENT.search(folded) else "sale" if _SALE.search(folded) else None
        return {"kind": kind, "deal": deal}
    return None


def is_seeking_reason(reason: str, text: str = "") -> bool:
    """Whether the AI's rejection says the author is looking for a property.

    Only the AI's own wording counts ("Author is seeking an apartment"), not the stock message
    used when it gave no reason, and the post has to mention a property at all.
    """
    said = (reason or "").lower()
    if not any(phrase in said for phrase in ("seeking", "looking for", "is asking", "wants to rent", "wants to buy", "يبحث عن")):
        return False
    return _PROPERTY_RE.search(_fold(text)) is not None


def remember(db, post, found: dict) -> bool:
    """Stores the request once (by its link). Returns True when it was new. Never raises."""
    import models

    url = (getattr(post, "postUrl", None) or "").strip()
    text = (getattr(post, "text", None) or "").strip()
    if not url or not text:
        return False
    try:
        if db.query(models.SeekerPost.id).filter(models.SeekerPost.post_url == url).first():
            return False
        location = ""
        try:
            from ad_location import UNKNOWN_LOCATION, settle_location

            location = settle_location(db, "", text)
            if location == UNKNOWN_LOCATION:
                location = ""
        except Exception:
            location = ""
        db.add(models.SeekerPost(
            post_url=url[:1000], author=(getattr(post, "author", None) or "")[:255] or None, text=text[:4000],
            kind=found.get("kind"), deal=found.get("deal"), location=location or None, posted_at=(getattr(post, "timestamp", None) or "")[:100] or None,
        ))
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

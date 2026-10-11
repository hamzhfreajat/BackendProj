"""
Text rules for the smart search.

The AI extracts most fields, but a few things are settled by the words of the
query themselves, and the AI gets them wrong often enough to matter: whether the
writer is looking for a property or offering one, rent or sale, the floor, the
furnishing and the rent period.

Pure logic (no DB, no network) so every reported query can be kept as a test;
see test_smart_search_text.py.

Every function takes `text`: the query after clean_text().
"""
import re
from typing import List, Optional

from arabic_utils import convert_hindi_numerals

# Arabic has no \b: a word ends where the letters end
_B = r"(?<![ء-ي])"
_E = r"(?![ء-ي])"


def clean_text(text: str) -> str:
    text = convert_hindi_numerals(text or "")
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ة", "ه")):
        text = text.replace(a, b)
    return text.lower()


# ---------------------------------------------------------------------------
# Looking for a property, or offering one
# ---------------------------------------------------------------------------

_DEMAND = re.compile(
    _B + r"(?:مطلوب|مطلوبه|بدور|بندور|ابحث|نبحث|بحاجه|محتاج|محتاجه|محتاجين"
    r"|وين بلاقي|وين الاقي|بدي استاجر|بدنا نستاجر|بدي اشتري|بدنا نشتري)" + _E
)
_POSTING = re.compile(r"(?:انزل|انشر|اضيف|اضافه|تنزيل|نشر)\s+اعلان")


def is_demand_post(text: str) -> bool:
    """"مطلوب شقة ... اللي عنده يبعتلي" is someone looking for a flat. The AI reads
    "اللي عنده" as an owner speaking and answers post_ad."""
    return bool(_DEMAND.search(text)) and not _POSTING.search(text)


# ---------------------------------------------------------------------------
# Rent or sale
# ---------------------------------------------------------------------------

_RENT_HINTS = re.compile(
    _B + r"(?:طالب|طالبه|طلاب|طالبات|مستاجر|مستاجره|استاجر|نستاجر|تاجير|اجره"
    r"|مفروش|مفروشه|يومي|يوميه|باليوم|اسبوعي|بالاسبوع|شهري|شهريا|بالشهر|سنوي|بالسنه|لمده)" + _E
)
_SALE_HINTS = re.compile(
    _B + r"(?:كاش|اقساط|بالاقساط|تقسيط|بالتقسيط|طابو|قوشان|تمويل|تملك|للتملك|استثمار|للاستثمار)" + _E
)
# In dinars: nobody rents for 10,000 a month and nobody buys a flat for 3,000
RENT_PRICE_CEILING = 3000
SALE_PRICE_FLOOR = 10000


def infer_deal(text: str, min_price: Optional[int] = None, max_price: Optional[int] = None) -> Optional[str]:
    """For a query that names neither rent nor sale: "rent", "sale", or None when
    the words do not settle it (the user is then asked)."""
    rent, sale = bool(_RENT_HINTS.search(text)), bool(_SALE_HINTS.search(text))
    if rent != sale:
        return "rent" if rent else "sale"
    price = max_price or min_price
    if price and not rent and not sale:
        if price >= SALE_PRICE_FLOOR:
            return "sale"
        if price <= RENT_PRICE_CEILING:
            return "rent"
    return None


# The same kind of property under "للبيع" and under "للايجار"
RENT_OF_SALE = {
    10301: 301,    # شقق
    10302: 302,    # ستوديوهات
    10101: 3101,   # فلل وقصور
    10102: 3102,   # بيوت مستقلة
    10103: 3103,   # دوبلكس / بنتهاوس
    10104: 3104,   # طابق كامل
    10105: 3105,   # ملحق / روف
    10853: 303,    # محلات
    18004: 304,    # مكاتب
}
SALE_OF_RENT = {rent_id: sale_id for sale_id, rent_id in RENT_OF_SALE.items()}


def align_category_with_deal(category_id: Optional[int], deal: Optional[str]) -> Optional[int]:
    """A rent query must not land in a sale category, and the other way round.
    A bare "شقة" maps to "شقق للبيع" in the dictionary, and the AI makes the same slip."""
    if deal == "rent":
        return RENT_OF_SALE.get(category_id, category_id)
    if deal == "sale":
        return SALE_OF_RENT.get(category_id, category_id)
    return category_id


# ---------------------------------------------------------------------------
# Floor
# ---------------------------------------------------------------------------

# The values the app's floor filter knows (and that ads are saved with)
FLOOR_BASEMENT = "طابق التسوية"
FLOOR_SEMI_GROUND = "طابق شبه أرضي"
FLOOR_GROUND = "الطابق الأرضي"
FLOOR_LAST = "طابق أخير"
FLOOR_OPTIONS = [FLOOR_BASEMENT, FLOOR_SEMI_GROUND, FLOOR_GROUND, "1", "2", "3", "4", "5", "6", "7",
                 FLOOR_LAST, "روف", "طابق أخير مع روف"]

_FLOOR_WORDS = {
    "ارضي": FLOOR_GROUND, "اول": "1", "ثاني": "2", "تاني": "2", "ثالث": "3", "تالت": "3",
    "رابع": "4", "خامس": "5", "سادس": "6", "سابع": "7", "اخير": FLOOR_LAST,
}
_FLOOR_WORD = r"(?:ال)?(?:" + "|".join(_FLOOR_WORDS) + r")" + _E
_FLOOR_ITEM = _FLOOR_WORD + r"|\d{1,2}(?!\d)"
# "طابق ارضي او اول", "الطابق الثاني والثالث", "طابق 2 او 3".
# After "و" or a comma only a word continues the list: "طابق اول و 3 غرف" is one floor.
_FLOOR_LIST = re.compile(
    _B + r"(?:ال)?طابق\s+((?:" + _FLOOR_ITEM + r")"
    r"(?:\s*او\s+(?:" + _FLOOR_ITEM + r")|\s*(?:و\s*|[،,/-]\s*)(?:" + _FLOOR_WORD + r"))*)"
)
_FLOOR_ITEM_RE = re.compile(_FLOOR_ITEM)
_SEMI_GROUND = re.compile(r"شبه\s+(?:ال)?ارضي")
_GROUND = re.compile(_B + r"(?:ال)?ارضي[ه]?" + _E)
_BASEMENT = re.compile(_B + r"(?:ال)?تسويه" + _E)


def mentions_floor(text: str) -> bool:
    return bool(re.search(_B + r"(?:ال)?(?:طابق|طوابق)" + _E, text))


def extract_floors(text: str) -> List[str]:
    """Floors the query names, as FLOOR_OPTIONS values."""
    found: List[str] = []

    def add(value: str):
        if value not in found:
            found.append(value)

    without_semi = text
    if _SEMI_GROUND.search(text):
        add(FLOOR_SEMI_GROUND)
        without_semi = _SEMI_GROUND.sub(" ", text)
    if _BASEMENT.search(text):
        add(FLOOR_BASEMENT)
    # "بيت ارضي", "شقة ارضية": the ground floor needs no "طابق" in front of it
    if _GROUND.search(without_semi):
        add(FLOOR_GROUND)
    for floor_list in _FLOOR_LIST.finditer(without_semi):
        for item in _FLOOR_ITEM_RE.findall(floor_list.group(1)):
            word = item[2:] if item.startswith("ال") else item
            add(_FLOOR_WORDS.get(word, word))
    return found


def floor_option(value) -> Optional[str]:
    """One of the AI's floor values ("الطابق الأرضي", 3, "٢", "الأول") as a FLOOR_OPTIONS value."""
    if value is None or isinstance(value, bool):
        return None
    raw = str(value).strip()
    if raw in FLOOR_OPTIONS:
        return raw
    text = clean_text(raw)
    if _SEMI_GROUND.search(text):
        return FLOOR_SEMI_GROUND
    digits = re.search(r"\d+", text)
    if digits:
        return digits.group(0)
    for word, option in _FLOOR_WORDS.items():
        if re.search(_B + r"(?:ال)?" + word + _E, text):
            return option
    if "تسويه" in text:
        return FLOOR_BASEMENT
    if "روف" in text:
        return "روف"
    return None


# ---------------------------------------------------------------------------
# Furnishing and rent period
# ---------------------------------------------------------------------------

FURNISHED, UNFURNISHED, PARTLY_FURNISHED = "مفروشة", "غير مفروشة", "مفروش جزئياً"

_UNFURNISHED = re.compile(
    r"غير\s+مفروش|مش\s+مفروش|بدون\s+(?:فرش|اثاث|عفش)|بلا\s+فرش|" + _B + r"(?:فارغ|فارغه|فاضي|فاضيه)" + _E
)
_PARTLY_FURNISHED = re.compile(r"(?:مفروش[ه]?|فرش)\s+جز[ءئ]ي|شبه\s+مفروش|نص\s+فرش")
_FURNISHED = re.compile(_B + r"(?:مفروش|مفروشه|معشيه|ماثثه|مؤثثه)" + _E)


def extract_furnishing(text: str) -> Optional[str]:
    if _UNFURNISHED.search(text):
        return UNFURNISHED
    if _PARTLY_FURNISHED.search(text):
        return PARTLY_FURNISHED
    if _FURNISHED.search(text):
        return FURNISHED
    return None


RENT_PERIODS = ["يومي", "أسبوعي", "شهري", "كل 3 أشهر", "كل أربع أشهر", "كل 5 أشهر", "كل 6 أشهر", "سنوي"]
# A short stay is a different product: monthly flats are no answer to "ليومين"
SHORT_STAY_PERIODS = {"يومي", "أسبوعي"}

_PERIOD_RULES = [
    # "ايام" only with a count in front of it: "خلال ايام" is not a daily rental
    ("يومي", re.compile(
        _B + r"(?:يومي|يوميه|يوميا|باليوم|يومين|ليله|ليلتين|ليالي|بالليله"
        r"|(?:\d+|ثلاث[ه]?|اربع[ه]?|خمس[ه]?|ست[ه]?|سبع[ه]?|عشر[ه]?)\s+ايام)" + _E
    )),
    ("أسبوعي", re.compile(_B + r"(?:اسبوع|اسبوعي|اسبوعيا|اسبوعين|اسابيع|بالاسبوع)" + _E)),
    ("شهري", re.compile(_B + r"(?:شهري|شهريا|بالشهر)" + _E)),
    ("سنوي", re.compile(_B + r"(?:سنوي|سنويا|بالسنه)" + _E)),
]


def extract_rent_period(text: str) -> Optional[str]:
    for period, pattern in _PERIOD_RULES:
        if pattern.search(text):
            return period
    return None

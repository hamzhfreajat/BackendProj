"""
Checks a price the AI extracted from a scraped post before it is saved.

The AI reads the post and returns one number. Most of the time it is the price, but
a look at the live ads showed the same slips again and again:

  * the plot or flat size taken as the price          ("750 متر" -> 750)
  * a price per metre or per dunum                    ("60 دينار للمتر" -> 60)
  * a monthly instalment or down payment of a sale    ("بدفعه 200 دينار" -> 200)
  * a number that is nowhere in the post              (5 for a 175 m flat)
  * a sale filed under rentals, or the reverse        ("للبيع ... 65 الف" as a rent of 65,000)
  * another country's currency                        (90,000,000)

Everything here works on the post's own text, with no database and no AI, so the
same post always gets the same answer and the rules can be tested.

An ad whose price fails the check is still saved, with no price: it stays in the
app and off the website, exactly like an ad that never stated one.
"""
import re
from typing import List, Optional, Tuple

# What a monthly/yearly rent and a sale price can be in Jordan, in JOD.
# Daily lets start around 10; a yearly rent rarely passes 30,000.
PLAUSIBLE = {"rent": (10, 30_000), "sale": (1_500, 15_000_000)}
# A "rent" at or above this, in a post that only talks about selling, is a sale
RENT_LOOKS_LIKE_SALE = 12_000

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_THOUSAND = {"الف", "الاف", "الفا", "k", "الفدينار"}
_MILLION = {"مليون", "ملايين"}
# Right after a number: it is a size, a count, an age or a distance, not money
_UNIT_AFTER = {
    "م", "م2", "م٢", "متر", "مترا", "امتار", "مترمربع", "دونم", "دونمات", "دنم", "دنمات", "غرف", "غرفه", "نوم", "حمام",
    "حمامات", "طابق", "طوابق", "سنه", "سنوات", "سنين", "شهر", "اشهر", "شهور", "كم", "كيلو", "كلم", "دقيقه", "دقائق", "دقايق",
    "شقق", "شقه", "قطع", "قطعه", "بلكونه", "مكيف", "اشخاص", "شخص", "واجهات", "شوارع", "محلات", "مخازن", "لبن", "لبنه",
}
_SIZE_UNITS = {"م", "م2", "م٢", "متر", "مترا", "امتار", "مترمربع", "دونم", "دونمات", "دنم", "دنمات", "كم", "كيلو", "كلم"}
# Right before a number: it is a size, a floor, a plot number or an age
_LABEL_BEFORE = {
    "مساحه", "المساحه", "مساحتها", "مساحته", "بمساحه", "مسطح", "طابق", "الطابق", "ط", "رقم", "حوض", "لوحه", "قطعه", "عمر",
    "العمر", "واجهه", "الواجهه", "عرض", "بعرض", "شارع", "هاتف", "تلفون", "موبايل", "واتس", "واتساب",
}
# The number is a price for one metre or one dunum, not for the property
_PER_UNIT = {"للمتر", "المتر", "للدونم", "الدونم", "للدنم", "الدنم", "متر", "دونم", "دنم"}
_PER_UNIT_LEAD = {"سعر", "السعر", "بسعر", "لكل", "للواحد", "الواحد"}
# The number is part of paying in parts
_INSTALMENT = {"شهري", "شهريا", "الشهري", "قسط", "القسط", "بقسط", "اقساط", "دفعه", "الدفعه", "بدفعه", "دفعات", "مقدم", "مقدما",
               "المقدم", "بمقدم", "عربون", "اولي", "الاولي"}
_RENT_WORDS = re.compile(r"(?<![ء-ي])(?:لل)?(?:ايجار|اجار|تاجير)(?![ء-ي])|(?<![ء-ي])(?:ال|لل)?اجر[هة](?![ء-ي])|(?<![ء-ي])يؤجر")
_SALE_WORDS = re.compile(r"(?<![ء-ي])(?:لل)?بيع(?![ء-ي])|(?<![ء-ي])تملك|(?<![ء-ي])للتملك")
# The number is introduced as the price itself
_TOTAL = {"سعر", "السعر", "بسعر", "سعرها", "سعره", "الاجمالي", "كامل", "نهائي", "المطلوب", "مطلوب", "ثمن", "الثمن", "بمبلغ"}
WINDOW = 3


def _fold(text: str) -> str:
    text = str(text or "").translate(_ARABIC_DIGITS)
    text = re.sub("[أإآ]", "ا", text).replace("ة", "ه").replace("ى", "ي")
    text = re.sub("[ً-ْـ]", "", text)
    # "65,000" / "65.000" / "65 000" are one number; "3.5" stays a decimal
    text = re.sub(r"(?<=\d)[,٬،](?=\d{3}(?!\d))", "", text)
    text = re.sub(r"(?<=\d)\.(?=\d{3}(?!\d))", "", text)
    # A dot only matters inside a decimal ("3.5"); elsewhere it is punctuation ("…..330")
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text)
    # Posts glue words to numbers ("160مطابق", "ب550")
    text = re.sub(r"(?<=\d)(?=[^\d\s.])|(?<=[^\d\s.])(?=\d)", " ", text)
    return re.sub(r"[^0-9A-Za-zء-ي.٪%]+", " ", text).lower()


def _numbers(tokens: List[str]) -> List[Tuple[float, int, int]]:
    """Every amount written in the post: (value, first token, last token)."""
    found = []
    for i, token in enumerate(tokens):
        if not re.fullmatch(r"\d+(?:\.\d+)?", token):
            continue
        value, last = float(token), i
        after = tokens[i + 1] if i + 1 < len(tokens) else ""
        # "25 الف", and "25 الفيوجد" where the next word is glued on
        if after in _THOUSAND or (after.startswith("الف") and not after.startswith("الفا")) or after.startswith("الاف"):
            # "65.000 الف" and "5000 الاف" already hold the thousands
            value, last = (value if value >= 1_000 else value * 1_000), i + 1
            # "23 الف ونصف"
            if tokens[i + 2: i + 3] in (["ونصف"], ["ونص"]):
                value, last = value + 500, i + 2
        elif after in _MILLION:
            value, last = value * 1_000_000, i + 1
            # "مليون و 600 الف"
            rest = tokens[i + 2: i + 5]
            if len(rest) == 3 and rest[0] == "و" and rest[1].isdigit() and rest[2].startswith("الف"):
                value, last = value + float(rest[1]) * 1_000, i + 4
        found.append((value, i, last))
    return found


def _glued(text: str, price: float) -> bool:
    """The price run together with what follows it: "الاجرة 53003نوم" (5300, then "3 نوم")
    or "الاجره 1150792846757" (115, then a phone number)."""
    if price != int(price):
        return False
    digits = re.sub(r"(?<=\d)[,٬،.](?=\d)", "", str(text or "").translate(_ARABIC_DIGITS))
    return re.search(r"(?<!\d)" + str(int(price)) + r"(?:\d(?!\d)|0?7[789]\d{7}(?!\d))", digits) is not None


def detect_deal(text: str) -> Optional[str]:
    """"rent" or "sale" when the post speaks of only one of them."""
    folded = _fold(text)
    rent, sale = bool(_RENT_WORDS.search(folded)), bool(_SALE_WORDS.search(folded))
    if rent and not sale:
        return "rent"
    if sale and not rent:
        return "sale"
    return None


def _is_money(tokens: List[str], first: int, last: int, deal: str) -> bool:
    """Whether the amount at this spot can be the price of the property."""
    after = tokens[last + 1: last + 1 + WINDOW]
    before = tokens[max(0, first - WINDOW): first]
    if last == first and after[:1] and after[0] in _UNIT_AFTER:
        # "750 متر" is a size at any value; "6000 طابق ارضي" is a rent followed by the floor
        if after[0] in _SIZE_UNITS or float(tokens[first]) < 100:
            return False
    if before[-1:] and before[-1] in _LABEL_BEFORE:
        return False
    # "60 دينار للمتر", "سعر الدونم 16 الف", "13 الف للدونم الواحد"
    if any(word in ("للمتر", "للدونم", "للدنم") for word in after):
        return False
    # Only when the two words right before it say so: "بمساحه 150 متر بسعر 78 الف" is a total
    if len(before) >= 2 and before[-1] in _PER_UNIT and before[-2] in _PER_UNIT_LEAD:
        return False
    # "السعر الاجمالي 55,000", "سعر كامل القطعه 13500 (يوجد امكانيه دفعه)": named as the price
    if any(word in _TOTAL for word in before):
        return True
    # "بدفعه 200", "دفعة أولى: 20,000", "قسط شهري 1,000", "500 دينار شهريا" in a sale
    if deal == "sale":
        following = [word for word in after[:2] if word not in ("دينار", "د", "jd", "jod")][:1]
        # After the number only "شهري" counts: in "28 الف دفعه اولي 10 الف" the 28 is the total
        if any(word in _INSTALMENT for word in before[-2:]) or any(word in ("شهري", "شهريا", "بالشهر") for word in following):
            return False
    return True


def check_price(price, deal: Optional[str], text: str) -> Tuple[float, str]:
    """(price to save, why). The price comes back as 0 when it cannot be trusted."""
    try:
        price = float(price or 0)
    except (TypeError, ValueError):
        return 0.0, "not a number"
    if price <= 0:
        return 0.0, "no price"
    if deal not in PLAUSIBLE:
        return price, "not real estate"

    tokens = _fold(text).split()
    spots = [(first, last) for value, first, last in _numbers(tokens) if abs(value - price) < 0.5]
    if not spots:
        if not _glued(text, price):
            return 0.0, "the price is not written in the post"
        spots = None
    if spots is not None and not any(_is_money(tokens, first, last, deal) for first, last in spots):
        return 0.0, "the number is a size, a per-metre price or an instalment"

    low, high = PLAUSIBLE[deal]
    if not low <= price <= high:
        return 0.0, f"outside {low:,}-{high:,} for a {deal}"
    return price, "ok"


def corrected_deal(price, deal: Optional[str], text: str) -> Optional[str]:
    """The deal the ad should be filed under when the post plainly says the other one.

    A flat "للبيع" at 65,000 that the AI put under rentals becomes a sale; a flat
    "للايجار" at 250 that it put under sales becomes a rental. Anything less clear
    keeps its category.
    """
    try:
        price = float(price or 0)
    except (TypeError, ValueError):
        return deal
    said = detect_deal(text)
    if deal == "rent" and said == "sale" and price >= RENT_LOOKS_LIKE_SALE:
        return "sale"
    # No rent is this high: with no word about renting in the post, it is a sale price
    if deal == "rent" and said != "rent" and PLAUSIBLE["rent"][1] < price <= PLAUSIBLE["sale"][1]:
        return "sale"
    if deal == "sale" and said == "rent" and 0 < price < PLAUSIBLE["sale"][0]:
        return "rent"
    return deal


# The same kind of property under rentals and under sales
_RENT_TO_SALE = {
    3: 2, 301: 10301, 302: 10302, 3101: 10101, 3102: 10102, 3103: 10103, 3104: 10104, 3105: 10105,
    303: 10303, 304: 10304, 310: 10310, 311: 10311, 314: 10314, 315: 10315,
}
_SALE_TO_RENT = {sale: rent for rent, sale in _RENT_TO_SALE.items()}
ROOTS = {"rent": 3, "sale": 2}


def deal_of_category(category_id, parents: dict) -> Optional[str]:
    """"rent" / "sale" for a real-estate category; `parents` maps category id -> parent id."""
    current, seen = category_id, set()
    while current is not None and current not in seen:
        seen.add(current)
        if current == ROOTS["rent"]:
            return "rent"
        if current == ROOTS["sale"]:
            return "sale"
        current = parents.get(current)
    return None


def category_for_deal(category_id, new_deal: str, parents: dict) -> int:
    """The matching category on the other side (the nearest level that has one)."""
    table = _RENT_TO_SALE if new_deal == "sale" else _SALE_TO_RENT
    current, seen = category_id, set()
    while current is not None and current not in seen:
        seen.add(current)
        if current in table and table[current] in parents:
            return table[current]
        current = parents.get(current)
    return ROOTS[new_deal]


# ---------------------------------------------------------------------------
# Reading a price out of a post that has none stored
# ---------------------------------------------------------------------------
# Words that introduce the price. The number has to follow one of them directly
# (a few filler words may sit in between), so a bare number is never taken.
_PRICE_LABEL = {
    "sale": {"السعر", "سعر", "بسعر", "سعرها", "سعره", "المطلوب", "مطلوب", "بمبلغ", "الثمن", "ثمن", "السعرالنهائي"},
    "rent": {"السعر", "سعر", "بسعر", "الاجره", "اجره", "اجرتها", "الايجار", "ايجار", "الاجار", "اجار", "ايجارها", "بايجار",
             "المطلوب", "مطلوب", "بمبلغ"},
}
_FILLER = {"النهائي", "نهائي", "الشهري", "شهري", "السنوي", "سنوي", "الاجمالي", "اجمالي", "الكلي", "كامل", "كاملا", "فقط", "هو",
           "هي", "ب", "بس", "القطعه", "الشقه", "البيت", "الارض", "المنزل", "الكامل", "كاش", "الكاش", "شامل", "مغري", "مميز",
           "مناسب", "حرق", "لقطه", "جدا", "الان", "حاليا", "للقطعه", "للشقه", "دينار", "اردني", "د"}
MAX_FILLERS = 3
_DAILY = re.compile(r"(?<![ء-ي])(?:يومي|يوميا|اليومي|باليوم|لليوم|ليله|الليله|لليله|بالليله)(?![ء-ي])")
# The post gives a range, a discount or several offers: no single price to take
_AMBIGUOUS = re.compile(
    r"(?<![ء-ي])(?:تبدا|تبدء|ابتداء|يبدا|تتراوح|يتراوح|اسعار|الاسعار|باسعار|اسعارنا|بدلا|بدل|كان|نزل|تنزيل|تخفيض|خصم|للمتر|للدونم|للدنم|للطالب|للطالبه|للشخص|للفرد|للسرير)(?![ء-ي])"
)


def extract_price(text: str, deal: Optional[str]) -> Tuple[float, str]:
    """(price, why) for a post that states exactly one clearly labelled price; (0, why) otherwise.

    Deliberately strict. It is used on ads that have no price, where taking nothing
    costs little and taking a wrong number puts a wrong price on the website.
    """
    if deal not in PLAUSIBLE:
        return 0.0, "not real estate"
    folded = _fold(text)
    if _AMBIGUOUS.search(folded):
        return 0.0, "a range, a discount or a per-unit price"
    said = detect_deal(text)
    if said is not None and said != deal:
        return 0.0, "the post is for the other deal"

    tokens = folded.split()
    low, high = PLAUSIBLE[deal]
    labelled, plausible_amounts = set(), set()
    for value, first, last in _numbers(tokens):
        if not _is_money(tokens, first, last, deal):
            continue
        if low <= value <= high and value >= (80 if deal == "rent" else 5_000):
            plausible_amounts.add(value)
        # Walk back over filler words to the label
        i, fillers = first - 1, 0
        while i >= 0 and tokens[i] in _FILLER and fillers < MAX_FILLERS:
            i, fillers = i - 1, fillers + 1
        if i < 0 or tokens[i] not in _PRICE_LABEL[deal]:
            continue
        # "سعر المتر 160", "سعر الدونم 16 الف" were already refused by _is_money; "ايجار 3 شهور" is a period
        if value < low or value > high:
            continue
        # "الاجرة 12,0004نوم": a number running into another number is not safe to read
        if tokens[last + 1: last + 2] and re.fullmatch(r"\d+(?:\.\d+)?", tokens[last + 1]):
            continue
        # A rent this low is only believable as a price per night
        if deal == "rent" and value < 80 and not _DAILY.search(folded):
            continue
        labelled.add(value)

    if len(labelled) != 1:
        return 0.0, "no labelled price" if not labelled else "several labelled prices"
    price = next(iter(labelled))
    # Another amount that could just as well be the price makes this one doubtful
    if any(other != price for other in plausible_amounts):
        return 0.0, "another amount could be the price"
    checked, reason = check_price(price, deal, text)
    return (checked, "ok") if checked else (0.0, reason)

"""
Tests for the ad titles the website shows (web_router.distinct_title).
Run with:  python test_distinct_title.py   (or pytest)
"""
from web_router import distinct_title

FLAT_RENT = "شقق للإيجار"


def test_adds_rooms_and_size_before_the_deal():
    assert distinct_title("شقة فاخرة للإيجار في الرابية", FLAT_RENT, 3, 150, None) == "شقة فاخرة 3 غرف 150م للإيجار في الرابية"


def test_adds_ground_floor():
    assert distinct_title("شقة فاخرة للإيجار في الرابية", FLAT_RENT, 2, None, "الطابق الأرضي") == "شقة فاخرة غرفتين طابق أرضي للإيجار في الرابية"


def test_never_repeats_what_the_title_says():
    assert distinct_title("شقة مفروشة 3 نوم للعائلات في دابوق – 170م", FLAT_RENT, 3, 170, None) == "شقة مفروشة 3 نوم للعائلات في دابوق – 170م"
    assert distinct_title("شقة أرضية فاخرة للإيجار", FLAT_RENT, None, None, "أرضي") == "شقة أرضية فاخرة للإيجار"


def test_leaves_out_a_room_count_too_small_for_the_size():
    # Scraped ads often say 1 bedroom for a 200 m² flat
    assert distinct_title("شقة فارغة للإيجار في ضاحية النخيل", FLAT_RENT, 1, 200, None) == "شقة فارغة 200م للإيجار في ضاحية النخيل"


def test_no_rooms_for_studios_or_land():
    assert distinct_title("استوديو مفروش للإيجار في الجبيهة", "استوديو للإيجار", 1, 45, None) == "استوديو مفروش 45م للإيجار في الجبيهة"
    assert distinct_title("أرض للبيع في ناعور", "أراضي للبيع", 3, 750, None) == "أرض 750م للبيع في ناعور"


def test_deal_word_followed_by_punctuation():
    assert distinct_title("شقة من المالك للايجار. موقع مميز", FLAT_RENT, 2, 85, None) == "شقة من المالك غرفتين 85م للايجار. موقع مميز"


def test_nothing_to_add():
    assert distinct_title("شقة للإيجار في خلدا", FLAT_RENT, None, None, None) == "شقة للإيجار في خلدا"


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name} {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)

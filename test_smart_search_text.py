"""
Regression tests for the smart search text rules.
Run with:  python test_smart_search_text.py   (or pytest)

Every case is a query a user reported, with the mistake it used to produce.
"""
from smart_search_text import (
    FLOOR_GROUND, FLOOR_LAST, FLOOR_SEMI_GROUND, FURNISHED, UNFURNISHED,
    align_category_with_deal, clean_text, extract_floors, extract_furnishing,
    extract_rent_period, floor_option, infer_deal, is_demand_post, mentions_floor,
)


def test_wanted_post_is_a_search_not_an_ad():
    # Opened the "add an ad" screen because of "يلي عندو يبعتلي"
    text = clean_text("مطلوب بيت مستقل في طبربور لحدود ١٥٠ الف يلي عندو يبعتلي\nللبيع")
    assert is_demand_post(text)
    assert is_demand_post(clean_text("صباح الخير بدور ع استديو مفروش قريب ل المطار الي عندو يبعثلي خاص او يعلق"))
    assert is_demand_post(clean_text("ابحث عن شقه للايجار قرب المؤسسه العسكريه"))
    assert is_demand_post(clean_text("وين بلاقي بيت غرفتين"))


def test_an_owner_is_not_a_wanted_post():
    assert not is_demand_post(clean_text("عندي شقة للبيع في خلدا"))
    assert not is_demand_post(clean_text("بدي انزل اعلان"))
    assert not is_demand_post(clean_text("مطلوب انزل اعلان عن شقتي"))


def test_deal_is_inferred_when_the_word_is_missing():
    # These three were answered with "للإيجار أم للبيع؟"
    assert infer_deal(clean_text("بدور على سكن في انحاء السابع، شارع مكة أو خلدا طالب جامعي")) == "rent"
    assert infer_deal(clean_text("بدور ع استديو مفروش قريب ل المطار")) == "rent"
    assert infer_deal(clean_text("شقة لمدة يومين في العقبة")) == "rent"
    # A budget settles it too
    assert infer_deal(clean_text("مطلوب بيت في طبربور"), max_price=150000) == "sale"
    assert infer_deal(clean_text("مطلوب شقة في اربد"), max_price=200) == "rent"
    assert infer_deal(clean_text("شقة في خلدا كاش")) == "sale"


def test_deal_stays_open_when_nothing_settles_it():
    # The user is asked: these could be either
    assert infer_deal(clean_text("مطلوب استديو في منطقة الياسمين وماحولها")) is None
    assert infer_deal(clean_text("مطلوب شقة في اربد بمساحه كبيره وشرط وجود ساحه خارجية")) is None
    assert infer_deal(clean_text("شقة مفروشة كاش")) is None


def test_rent_query_never_lands_in_a_sale_category():
    # "بحاجه لغرفه ... للاجار" / a bare "شقة" used to open "شقق للبيع"
    assert align_category_with_deal(10301, "rent") == 301
    assert align_category_with_deal(10302, "rent") == 302
    assert align_category_with_deal(10102, "rent") == 3102
    assert align_category_with_deal(301, "sale") == 10301
    # Already on the right side, or nothing to compare with
    assert align_category_with_deal(301, "rent") == 301
    assert align_category_with_deal(10301, None) == 10301
    assert align_category_with_deal(None, "rent") is None
    # No counterpart: left alone
    assert align_category_with_deal(19000, "rent") == 19000


def test_ground_floor():
    # "ما بختار ارضي": the ground floor was never selected
    assert extract_floors(clean_text("السلام عليكم \nمطلوب بيت ارضي للإيجار")) == [FLOOR_GROUND]
    assert extract_floors(clean_text("مطلوب شقة للايجار طابق ارضي فارغه\nالعقبة")) == [FLOOR_GROUND]
    assert extract_floors(clean_text("شقة ارضية للبيع")) == [FLOOR_GROUND]
    assert extract_floors(clean_text("شقة شبه ارضي")) == [FLOOR_SEMI_GROUND]
    # Land is not a floor
    assert extract_floors(clean_text("ارض للبيع في ناعور")) == []
    assert extract_floors(clean_text("اراضي للبيع")) == []


def test_several_floors():
    # "ما بطلعلي الأرضي والاول"
    assert extract_floors(clean_text("مطلوب شقه للايجار طابق ارضي او اول هندسي")) == [FLOOR_GROUND, "1"]
    assert extract_floors(clean_text("الطابق الثاني والثالث")) == ["2", "3"]
    assert extract_floors(clean_text("طابق 2 او 3")) == ["2", "3"]
    assert extract_floors(clean_text("طابق تاني")) == ["2"]
    assert extract_floors(clean_text("طابق اخير")) == [FLOOR_LAST]


def test_floor_list_stops_at_other_numbers():
    assert extract_floors(clean_text("طابق اول و 3 غرف نوم")) == ["1"]
    assert extract_floors(clean_text("طابق ثالث، 2 حمام")) == ["3"]
    # Aqaba neighbourhoods and Amman circles are not floors
    assert extract_floors(clean_text("شقة للايجار في الثالثه العقبه")) == []
    assert extract_floors(clean_text("شقة قرب الدوار السابع")) == []
    assert extract_floors(clean_text("ثلاث غرف نوم وصالون وثلاث حمامات")) == []


def test_floor_values_are_the_ones_the_app_filters_by():
    # The app's filter knows "1", not "الطابق الأول": that chip was never selected
    assert floor_option("الطابق الأول") == "1"
    assert floor_option(2) == "2"
    assert floor_option("٣") == "3"
    assert floor_option("الطابق الأرضي") == FLOOR_GROUND
    assert floor_option("طابق شبه أرضي") == FLOOR_SEMI_GROUND
    assert floor_option("طابق أخير مع روف") == "طابق أخير مع روف"
    assert floor_option(None) is None
    assert floor_option("") is None


def test_mentions_floor():
    assert mentions_floor(clean_text("شقة طابق ثاني"))
    assert mentions_floor(clean_text("الطابق الثالث"))
    assert not mentions_floor(clean_text("مطلوب بيت غرفتين"))


def test_furnishing():
    # "فارغه" was ignored
    assert extract_furnishing(clean_text("مطلوب شقة للايجار طابق ارضي فارغه")) == UNFURNISHED
    assert extract_furnishing(clean_text("شقة غير مفروشة")) == UNFURNISHED
    assert extract_furnishing(clean_text("شقة بدون فرش")) == UNFURNISHED
    assert extract_furnishing(clean_text("مطلوب شقة مفروشة نظيفة")) == FURNISHED
    assert extract_furnishing(clean_text("استديو مفروش")) == FURNISHED
    assert extract_furnishing(clean_text("شقة غرفتين")) is None


def test_rent_period():
    # "مش مختار خيار شقه يومي"
    text = clean_text("مطلوب شقه صغيره مفروشه للإيجار لشخصين في طبربور او حولها لمده يومين الى ثلاث ايام.")
    assert extract_rent_period(text) == "يومي"
    assert extract_rent_period(clean_text("شاليه لليلة واحدة")) is None  # "لليلة" carries a prefix, the AI handles it
    assert extract_rent_period(clean_text("شقة ايجار يومي")) == "يومي"
    assert extract_rent_period(clean_text("شقة لمدة اسبوع")) == "أسبوعي"
    assert extract_rent_period(clean_text("الايجار شهري")) == "شهري"
    assert extract_rent_period(clean_text("مطلوب خلال ايام شقة للايجار")) is None
    assert extract_rent_period(clean_text("شقة للايجار")) is None


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

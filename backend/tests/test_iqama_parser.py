from app.parsers import parse_iqama


RAW_IQAMA_OCR = """هوية مقيم
محمد سليم محمد نسيم
رقم الهوية: ٢٥٧٢٣١٢٠٨٦
تاريخ الميلاد: ١٩٨٨/٠٨/٠٨
الجنسية: الهند
تاريخ الانتهاء: ٢٠٢٦/١٠/٠٦
"""


def test_parse_iqama_extracts_arabic_labeled_fields():
    parsed = parse_iqama(RAW_IQAMA_OCR)

    assert parsed["name"] == "محمد سليم محمد نسيم"
    assert parsed["id_number"] == "2572312086"
    assert parsed["iqama_number"] == "2572312086"
    assert parsed["nationality"] == "الهند"
    assert parsed["dob"] == "1988/08/08"
    assert parsed["doe"] == "2026/10/06"


def test_residency_alias_keeps_iqama_fields_available():
    from app.parsers import parse_residency

    parsed = parse_residency(RAW_IQAMA_OCR)

    assert parsed["iqama_number"] == "2572312086"
    assert parsed["nationality"] == "الهند"


def test_resident_name_label_maps_to_unified_name_field():
    parsed = parse_iqama(
        "اسم صاحب الإقامة: محمد سليم محمد نسيم\n"
        "رقم الهوية : ٢٥٧٢٣١٢٠٨٦"
    )

    assert parsed["name"] == "محمد سليم محمد نسيم"


def test_resident_name_value_can_follow_label_on_next_line():
    parsed = parse_iqama(
        "اسم صاحب الاقامة\n"
        "محمد سليم محمد نسيم\n"
        "رقم الهوية\n"
        "٢٥٧٢٣١٢٠٨٦"
    )

    assert parsed["name"] == "محمد سليم محمد نسيم"
    assert parsed["id_number"] == "2572312086"


def test_iqama_name_prefers_top_resident_name_over_employer_name():
    text = """هوية مقيم
محمد سليم محمد نسيم
MOHAMMAD SALEEM MOHAMMAD NASEEM
رقم الهوية: ٢٥٧٢٣١٢٠٨٦
اسم صاحب العمل: مؤسسة وليد علي عمر باشميل للمقاولات
"""

    assert parse_iqama(text)["name"] == "محمد سليم محمد نسيم"


def test_iqama_fields_can_be_on_the_next_line():
    text = """هوية مقيم
الاسم:
محمد سليم محمد نسيم
رقم الهوية:
٢٥٧٢٣١٢٠٨٦
الجنسية:
الهند
"""

    parsed = parse_iqama(text)

    assert parsed["name"] == "محمد سليم محمد نسيم"
    assert parsed["id_number"] == "2572312086"
    assert parsed["nationality"] == "الهند"


def test_iqama_supports_rtl_label_order_and_english_name():
    parsed = parse_iqama(
        "محمد سليم محمد نسيم\n"
        "MOHAMMAD SALEEM MOHAMMAD NASEEM\n"
        "الهند الجنسية:\n"
        "رقم الهوية: ٢٥٧٢٣١٢٠٨٦",
        language="en",
    )

    assert parsed["name"] == "MOHAMMAD SALEEM MOHAMMAD NASEEM"
    assert parsed["name_ar"] == "محمد سليم محمد نسيم"
    assert parsed["name_en"] == "MOHAMMAD SALEEM MOHAMMAD NASEEM"
    assert parsed["nationality"] == "الهند"
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
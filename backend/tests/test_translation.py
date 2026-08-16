from app.translation import choose_name, choose_value


def test_choose_name_prefers_name_in_requested_language():
    assert choose_name("محمد", "MOHAMMAD", "ar") == "محمد"
    assert choose_name("محمد", "MOHAMMAD", "en") == "MOHAMMAD"


def test_choose_name_falls_back_to_other_language(monkeypatch):
    monkeypatch.setattr(
        "app.translation.translate_text",
        lambda value, source, target: "MOHAMMAD" if target == "en" else "محمد",
    )

    assert choose_name("محمد", "", "en") == "MOHAMMAD"
    assert choose_name("", "MOHAMMAD", "ar") == "محمد"


def test_choose_value_translates_non_name_fields(monkeypatch):
    monkeypatch.setattr(
        "app.translation.translate_text",
        lambda value, source, target: "Heavy Transport" if target == "en" else "نقل ثقيل",
    )

    assert choose_value("نقل ثقيل", "", "en") == "Heavy Transport"
    assert choose_value("", "Heavy Transport", "ar") == "نقل ثقيل"
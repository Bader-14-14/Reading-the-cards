from app.translation import choose_name


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
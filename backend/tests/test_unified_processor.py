from fastapi.testclient import TestClient

from app.main import app
from app.unified_processor import classify_card_text


CLIENT = TestClient(app)


def test_card_classification_uses_content_not_filename():
    assert classify_card_text("هوية مقيم رقم الهوية").card_type == "iqama"
    assert classify_card_text("مقيم هوية رقم الهوية الجنسية").card_type == "iqama"
    assert classify_card_text("رخصة قيادة License").card_type == "driving_license"
    assert classify_card_text("استمارة رخصة سير").card_type == "vehicle_registration"
    assert classify_card_text("الهوية الوطنية National ID").card_type == "national_id"


def test_unified_endpoint_accepts_one_or_many_and_keeps_errors_per_file(monkeypatch):
    calls = []

    def fake_process(image_bytes, *, provider, language):
        calls.append(image_bytes)
        if image_bytes == b"bad":
            raise ValueError("bad image")
        return {
            "card_type": "iqama",
            "classification_confidence": "high",
            "language": language,
            "data": {"name": "test", "id_number": "2422262553"},
            "missing_fields": ["nationality"],
        }

    monkeypatch.setattr("app.main.process_card", fake_process)
    response = CLIENT.post(
        "/extract-cards?language=en",
        files=[
            ("files", ("random-name.bin", b"good", "image/jpeg")),
            ("files", ("another-name", b"bad", "image/jpeg")),
        ],
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert results[0]["card_type"] == "iqama"
    assert results[0]["filename"] == "random-name.bin"
    assert results[1]["error"] == "Card processing failed."
    assert calls == [b"good", b"bad"]

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


CLIENT = TestClient(app)
IMAGE_PATH = Path(r"C:\Users\DELL\Desktop\Card\ID.jpg")


def test_extract_saudi_id_endpoint_returns_expected_fields():
    assert IMAGE_PATH.exists(), f"Test image not found: {IMAGE_PATH}"

    with IMAGE_PATH.open("rb") as fh:
        response = CLIENT.post(
            "/extract-saudi-id?language=ar",
            files={"file": (IMAGE_PATH.name, fh.read(), "image/jpeg")},
        )

    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["filename"] == IMAGE_PATH.name
    assert payload["language"] == "ar"

    data = payload["data"]
    assert data["id_number"] == "1033541622"
    assert data["dob"] == "17/01/1980"
    assert data["doe"] == "03/02/2031"
    assert "بدر" in data["name"]
    assert "شليان" in data["name"]

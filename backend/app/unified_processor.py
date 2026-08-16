"""Content-based dispatch for single and batch card extraction."""

from dataclasses import dataclass

from .ocr_providers import detect_text_azure, detect_text_tesseract, parse_document, parse_document_saudi_id

MAX_BATCH_FILES = 20
MAX_FILE_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class CardClassification:
    card_type: str
    confidence: str


def classify_card_text(text: str) -> CardClassification:
    """Classify a card from OCR content, never from its filename."""
    normalized = (text or "").lower()
    if "الهوية الوطنية" in normalized or "national id" in normalized:
        return CardClassification("national_id", "high")
    if "هوية مقيم" in normalized or "iqama" in normalized or "رقم الإقامة" in normalized:
        return CardClassification("iqama", "high")
    if "رخصة قيادة" in normalized or "driving license" in normalized:
        return CardClassification("driving_license", "high")
    if "رخصة سير" in normalized or "vehicle registration" in normalized or "استمارة" in normalized:
        return CardClassification("vehicle_registration", "high")
    return CardClassification("unknown", "low")


def _missing_fields(card_type: str, data: dict) -> list[str]:
    required = {
        "national_id": ("name", "id_number", "dob", "doe"),
        "iqama": ("name", "id_number", "nationality", "dob", "doe"),
        "driving_license": ("name", "license_number", "expiry"),
        "vehicle_registration": ("owner", "plate"),
    }.get(card_type, ())
    return [field for field in required if not data.get(field)]


def process_card(image_bytes: bytes, *, provider: str = "azure", language: str = "ar") -> dict:
    """Process one image; batch processing calls this exact function repeatedly."""
    text = detect_text_azure(image_bytes) if provider == "azure" else detect_text_tesseract(image_bytes)
    classification = classify_card_text(text)

    if classification.card_type == "national_id":
        data = parse_document_saudi_id(image_bytes, language=language)
    elif classification.card_type == "iqama":
        data = parse_document("iqama", image_bytes, provider=provider, language=language)
    elif classification.card_type == "driving_license":
        data = parse_document("license", image_bytes, provider=provider, language=language)
    elif classification.card_type == "vehicle_registration":
        data = parse_document("vehicle", image_bytes, provider=provider, language=language)
    else:
        data = {"raw_text": text}

    return {
        "card_type": classification.card_type,
        "classification_confidence": classification.confidence,
        "language": language,
        "data": data,
        "missing_fields": _missing_fields(classification.card_type, data),
    }

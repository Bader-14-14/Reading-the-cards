import os
import io
import requests
from PIL import Image

try:
    import pytesseract
except Exception:
    pytesseract = None


def _image_from_bytes(b):
    return Image.open(io.BytesIO(b))


def detect_text_tesseract(image_bytes: bytes) -> str:
    if pytesseract is None:
        raise RuntimeError('pytesseract not installed')
    img = _image_from_bytes(image_bytes)
    # Use both English and Arabic if available
    try:
        text = pytesseract.image_to_string(img, lang='eng+ara')
    except Exception:
        text = pytesseract.image_to_string(img)
    return text


def detect_text_azure(image_bytes: bytes) -> str:
    endpoint = os.environ.get('AZURE_OCR_ENDPOINT')
    key = os.environ.get('AZURE_OCR_KEY')
    if not endpoint or not key:
        raise RuntimeError('Azure OCR not configured (set AZURE_OCR_ENDPOINT and AZURE_OCR_KEY)')
    ocr_url = endpoint.rstrip('/') + '/vision/v3.2/ocr?language=unk&detectOrientation=true'
    headers = {'Ocp-Apim-Subscription-Key': key, 'Content-Type': 'application/octet-stream'}
    resp = requests.post(ocr_url, headers=headers, data=image_bytes)
    resp.raise_for_status()
    data = resp.json()
    lines = []
    for region in data.get('regions', []):
        for line in region.get('lines', []):
            words = [w.get('text', '') for w in line.get('words', [])]
            lines.append(' '.join(words))
    return '\n'.join(lines)


def parse_document(document_type: str, image_bytes: bytes, provider: str = 'azure') -> dict:
    """Return parsed fields for the given document type.
    provider: 'azure' | 'local'
    """
    text = ''
    if provider == 'local':
        text = detect_text_tesseract(image_bytes)
    else:
        try:
            text = detect_text_azure(image_bytes)
        except Exception:
            # fallback to local if azure fails
            text = detect_text_tesseract(image_bytes)

    # very naive extraction: return raw_text and placeholders
    result = {'raw_text': text}
    if document_type == 'id':
        result.update({'name': '', 'id_number': '', 'dob': ''})
    elif document_type == 'license':
        result.update({'name': '', 'license_number': '', 'expiry': ''})
    elif document_type == 'vehicle':
        result.update({'plate': '', 'owner': ''})
    elif document_type == 'residency':
        result.update({'name': '', 'iqama_number': '', 'nationality': ''})
    else:
        # generic
        result.update({'fields': {}})
    return result

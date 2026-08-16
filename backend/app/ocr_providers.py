import os
import io
import time
import requests
from PIL import Image, ImageOps, ImageFilter, ImageEnhance

try:
    import pytesseract
except Exception:
    pytesseract = None


def _image_from_bytes(b):
    return Image.open(io.BytesIO(b))


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Conservative preprocessing to improve OCR quality on Saudi ID cards."""
    img = img.convert('RGB')
    width, height = img.size
    if max(width, height) < 1600:
        scale = 2.0
        img = img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)

    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = img.filter(ImageFilter.SHARPEN)

    width, height = img.size
    if max(width, height) > 2200:
        scale = 2200 / max(width, height)
        img = img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)

    # Binarize with a moderate threshold for printed ID cards.
    img = img.point(lambda p: 255 if p > 180 else 0)
    return img


def detect_text_tesseract(image_bytes: bytes) -> str:
    if pytesseract is None:
        raise RuntimeError('pytesseract not installed')
    img = _image_from_bytes(image_bytes)
    try:
        if os.name == 'nt':
            possible = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(possible):
                pytesseract.pytesseract.tesseract_cmd = possible

        processed = _preprocess_image(img)
        try:
            text = pytesseract.image_to_string(processed, lang='ara+eng', config='--psm 6')
        except Exception:
            try:
                text = pytesseract.image_to_string(processed, lang='eng+ara', config='--psm 6')
            except Exception:
                text = pytesseract.image_to_string(processed, config='--psm 6')
    except Exception:
        raise
    return text


def detect_text_azure(image_bytes: bytes) -> str:
    endpoint = os.environ.get('AZURE_OCR_ENDPOINT')
    key = os.environ.get('AZURE_OCR_KEY')
    if not endpoint or not key:
        raise RuntimeError('Azure OCR not configured (set AZURE_OCR_ENDPOINT and AZURE_OCR_KEY)')
    headers = {'Ocp-Apim-Subscription-Key': key, 'Content-Type': 'application/octet-stream'}
    analyze_url = endpoint.rstrip('/') + '/documentintelligence/documentModels/prebuilt-read:analyze?api-version=2024-11-30'
    response = None
    for attempt in range(3):
        response = requests.post(analyze_url, headers=headers, data=image_bytes, timeout=30)
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
            break
        retry_after = response.headers.get('Retry-After')
        try:
            delay = min(float(retry_after), 10.0) if retry_after else 2.0 ** attempt
        except ValueError:
            delay = 2.0 ** attempt
        time.sleep(delay)
    if response.status_code == 202:
        operation_url = response.headers.get('Operation-Location')
        if not operation_url:
            raise RuntimeError('Azure OCR did not return an operation location')
        result = None
        for _ in range(20):
            poll = requests.get(operation_url, headers={'Ocp-Apim-Subscription-Key': key}, timeout=30)
            if poll.status_code in {429, 500, 502, 503, 504}:
                time.sleep(2.0 ** min(attempt, 3))
                continue
            poll.raise_for_status()
            result = poll.json()
            if result.get('status') in ('succeeded', 'failed'):
                break
            time.sleep(0.5)
        if not result or result.get('status') != 'succeeded':
            raise RuntimeError('Azure OCR analysis did not succeed')
        return result.get('analyzeResult', {}).get('content', '')
    response.raise_for_status()
    return response.json().get('analyzeResult', {}).get('content', '')


from .parsers import parse_id, parse_license, parse_vehicle, parse_iqama
from .saudi_id_extractor import extract_saudi_id


def parse_document(document_type: str, image_bytes: bytes, provider: str = 'azure', language: str = 'ar') -> dict:
    """Return parsed fields for the given document type using OCR then heuristics.
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

    if document_type == 'id':
        return parse_id(text)
    elif document_type == 'license':
        return parse_license(text)
    elif document_type == 'vehicle':
        return parse_vehicle(text)
    elif document_type in ('residency', 'iqama'):
        return parse_iqama(text, language=language)
    else:
        return {'raw_text': text}


def parse_document_saudi_id(image_bytes: bytes, language: str = 'ar') -> dict:
    """
    Extract fields from Saudi ID card using region-based OCR.
    
    Args:
        image_bytes: Raw image data
        language: 'ar' for Arabic name, 'en' for English name
    
    Returns:
        Dictionary with extracted fields: name, id_number, dob, doe, raw_text
    """
    return extract_saudi_id(image_bytes, language=language)

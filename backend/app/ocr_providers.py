import os
import io
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


from .parsers import parse_id, parse_license, parse_vehicle, parse_residency
from .saudi_id_extractor import extract_saudi_id


def parse_document(document_type: str, image_bytes: bytes, provider: str = 'azure') -> dict:
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
    elif document_type == 'residency':
        return parse_residency(text)
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

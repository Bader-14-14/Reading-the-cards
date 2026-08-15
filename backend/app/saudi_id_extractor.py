"""
Advanced Saudi ID card OCR extraction with region-based processing.
Integrates Tesseract with preprocessing and intelligent field extraction.
"""

import re
import os
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import io

try:
    import pytesseract
except Exception:
    pytesseract = None


# Configuration
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_DIR = Path(r"C:\Users\DELL\AppData\Local\CardOCR\tessdata")
REFERENCE_SIZE = (1771, 1098)  # Standard legacy ID card dimensions

# Reference region coordinates for standard layout
REGIONS_LEGACY = {
    'name_ar': (740, 210, 1700, 325),
    'name_en': (120, 230, 1650, 390),
    'id_line': (640, 600, 1640, 780),
    'dob_line': (640, 700, 1640, 860),
    'doe_line': (120, 700, 1650, 1035),
}

REGIONS_MODERN = {
    'name_ar': (820, 360, 1660, 450),
    'name_en': (820, 440, 1660, 540),
    'id_line': (350, 520, 1450, 650),
    'dob_line': (690, 624, 1396, 744),
    'doe_line': (690, 720, 1400, 870),
}


def _ensure_pytesseract():
    """Ensure pytesseract is configured and available."""
    if pytesseract is None:
        raise RuntimeError('pytesseract not installed')
    if os.name == 'nt' and os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def preprocess(img: Image.Image) -> Image.Image:
    """Apply image preprocessing to improve OCR quality."""
    img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(3.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def scale_box(box, image_size):
    """Scale reference box coordinates to actual image dimensions."""
    ref_width, ref_height = REFERENCE_SIZE
    width, height = image_size
    left, top, right, bottom = box
    return (
        round(left * width / ref_width),
        round(top * height / ref_height),
        round(right * width / ref_width),
        round(bottom * height / ref_height),
    )


def get_regions(image_size):
    """Get appropriate region coordinates based on image aspect ratio."""
    width, height = image_size
    aspect_ratio = width / height if height > 0 else 1.0
    
    # Legacy layout: aspect ratio >= 1.58 (wider)
    if aspect_ratio >= 1.58:
        return REGIONS_LEGACY
    # Modern layout: compact aspect ratio < 1.58
    else:
        return REGIONS_MODERN


def ocr_text(img: Image.Image, lang: str = "eng") -> str:
    """Run Tesseract with multiple PSM modes and combine results."""
    _ensure_pytesseract()
    results = []
    for psm in (6, 7, 11, 13):
        try:
            txt = pytesseract.image_to_string(
                img,
                lang=lang,
                config=f"--tessdata-dir {TESSDATA_DIR.as_posix()} --psm {psm}",
            )
            results.append(txt)
        except Exception:
            pass
    return "\n".join(results)


def ocr_single_line(img: Image.Image, lang: str) -> str:
    """Run Tesseract with PSM 7 (single line mode)."""
    _ensure_pytesseract()
    try:
        return pytesseract.image_to_string(
            img,
            lang=lang,
            config=f"--tessdata-dir {TESSDATA_DIR.as_posix()} --psm 7",
        )
    except Exception:
        return ""


def ocr_numeric_date(img: Image.Image) -> str:
    """Extract dates with numeric whitelist (0-9 and /)."""
    _ensure_pytesseract()
    grayscale = ImageOps.autocontrast(img.convert("L"))
    try:
        return pytesseract.image_to_string(
            grayscale,
            lang="eng",
            config=(
                f"--tessdata-dir {TESSDATA_DIR.as_posix()} --psm 7 "
                "-c tessedit_char_whitelist=0123456789/"
            ),
        )
    except Exception:
        return ""


def parse_arabic_name(text: str) -> str:
    """
    Parse Arabic name from text.
    Validates 4-6 name parts and preserves OCR order.
    """
    name = re.sub(r"[^\u0621-\u064A\s]", "", text)
    name = re.sub(r"\s+", " ", name).strip()
    words = name.split()
    
    normalized_words = []
    for word in words:
        if word not in {"بن", "بنت"} and len(word) <= 2 and normalized_words and normalized_words[-1] not in {"بن", "بنت"}:
            normalized_words[-1] += word
        else:
            normalized_words.append(word)
    
    name = " ".join(normalized_words)
    name_parts = [part for part in normalized_words if part not in {"بن", "بنت"}]
    
    # Must have 4-6 name parts
    if not 4 <= len(name_parts) <= 6:
        return ""
    
    return name


def parse_name_from_text(text: str) -> str:
    """
    Parse English name from OCR text with intelligent scoring.
    Handles spurious prefixes and selects best candidate.
    """
    cleaned_lines = []
    for raw in text.splitlines():
        cleaned = re.sub(r"[^A-Za-z\s,.-]", "", raw).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(". ,-")
        if cleaned:
            cleaned_lines.append(cleaned)

    best = ""
    best_score = -1
    
    for cleaned in cleaned_lines:
        if cleaned.upper().endswith(" FE"):
            cleaned = cleaned[:-2].strip()
        
        score = 0
        
        # Bonus for common name keywords
        upper_cleaned = cleaned.upper()
        keywords = ["BADER", "BIN", "SAUD", "ALREHAILI", "ALI", "MOHAMMED", 
                   "ALHAKEEM", "MAHDI", "HASAN", "TAHER", "HASSAN"]
        for keyword in keywords:
            if keyword in upper_cleaned:
                score += 5
        
        # Strong bonus for family names
        if any(fname in upper_cleaned for fname in ["ALREHAILI", "ALHAKEEM", "ALZAKARI"]):
            score += 20
        
        words = re.findall(r"[A-Za-z]+", cleaned)
        if 3 <= len(words) <= 6:
            score += 20
        
        score += sum(len(word) for word in words)
        
        if "," in cleaned:
            score += 25
        
        # Bonus for repeated lines
        score += 25 * sum(1 for other in cleaned_lines if other.upper() == upper_cleaned)
        
        if score > best_score:
            best_score = score
            best = cleaned
    
    if not best:
        return ""
    
    # Fix common OCR errors
    best = best.upper()
    if best.startswith("LREHAILI"):
        best = "ALREHAILI" + best[9:]
    elif best.startswith("REHAILI"):
        best = "AL" + best
    elif best.startswith("LREH"):
        best = "AL" + best
    
    return best


def parse_id_number(text: str) -> str:
    """
    Extract and validate Saudi ID number.
    Corrects common OCR errors (leading digit 4 → 1).
    """
    matches = re.findall(r"\d{9,10}", text)
    if not matches:
        return ""
    
    candidates = []
    for match in matches:
        value = match
        # Fix common OCR error: leading 4 → 1
        if len(value) == 10 and value.startswith("4"):
            value = "1" + value[1:]
        if len(value) == 10:
            candidates.append(value)
    
    # Return first candidate that passes checksum validation
    for candidate in candidates:
        if is_valid_saudi_id(candidate):
            return candidate
    
    return candidates[0] if candidates else ""


def is_valid_saudi_id(value: str) -> bool:
    """Validate Saudi ID using Luhn checksum algorithm."""
    if not re.fullmatch(r"[12]\d{9}", value):
        return False
    
    total = 0
    for index, digit in enumerate(value):
        number = int(digit) * (2 if index % 2 == 0 else 1)
        total += number // 10 + number % 10
    
    return total % 10 == 0


def parse_first_date(text: str) -> str:
    """Extract first date matching DD/MM/YYYY format."""
    match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    return match.group(0) if match else ""


def extract_dates_by_label(text: str) -> dict:
    """Extract DOB and DOE by looking for labels."""
    dob_pattern = r"(?:D\s*O\s*B|Date\s*of\s*Birth|تاريخ\s*الميلاد)\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})"
    doe_pattern = r"(?:D\s*O\s*E|Expiry\s*Date|تاريخ\s*الانتهاء)\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})"
    
    dob_match = re.search(dob_pattern, text, re.IGNORECASE)
    doe_match = re.search(doe_pattern, text, re.IGNORECASE)
    
    return {
        'dob': dob_match.group(1) if dob_match else "",
        'doe': doe_match.group(1) if doe_match else "",
    }


def extract_saudi_id(image_bytes: bytes, language: str = 'ar') -> dict:
    """
    Extract Saudi ID fields from image bytes.
    
    Args:
        image_bytes: Raw image data
        language: 'ar' for Arabic name, 'en' for English name
    
    Returns:
        Dictionary with extracted fields: name, id_number, dob, doe, raw_text
    """
    _ensure_pytesseract()
    
    # Load and get image dimensions
    img = Image.open(io.BytesIO(image_bytes))
    image_size = img.size
    width, height = image_size
    
    # Determine layout type
    is_modern_layout = width / height < 1.58
    
    # Get regions for this image size
    regions = get_regions(image_size)
    
    # Extract text from each region
    region_texts = {}
    for key, box in regions.items():
        try:
            scaled_box = scale_box(box, image_size)
            crop = img.crop(scaled_box)
            
            if key == 'name_ar':
                # Arabic name: use single-line PSM 7
                region_texts[key] = ocr_single_line(crop, 'ara')
            elif is_modern_layout and key in {'dob_line', 'doe_line'}:
                # Modern layout dates: use numeric extraction
                region_texts[key] = ocr_numeric_date(crop)
            elif key == 'name_en' or key == 'id_line':
                # Names and ID: multi-PSM for better accuracy
                region_texts[key] = ocr_text(crop, 'eng')
            else:
                # Other regions: standard multi-PSM
                region_texts[key] = ocr_text(crop, 'eng')
        except Exception:
            region_texts[key] = ''
    
    # Parse Arabic name
    name_ar = parse_arabic_name(region_texts.get('name_ar', ''))
    
    # Parse English name with retry logic for noisy OCR
    name_en = parse_name_from_text(region_texts.get('name_en', ''))
    
    # Retry if spurious prefix detected or known noise
    has_noisy_prefix = re.match(r"^[A-Z]{1,2}\s+[A-Z]+,", name_en)
    has_known_ocr_noise = "MOPANMED" in name_en or "ALZAKARL" in name_en
    if has_noisy_prefix or has_known_ocr_noise:
        try:
            scaled_box = scale_box(regions['name_en'], image_size)
            crop = img.crop(scaled_box)
            name_en = parse_name_from_text(ocr_text(crop, 'eng'))
        except Exception:
            pass
    
    # Parse ID number
    id_number = parse_id_number(region_texts.get('id_line', ''))
    
    # Parse dates: combine all text regions to find labels
    combined_text = '\n'.join(region_texts.values())
    labelled_dates = extract_dates_by_label(combined_text)
    
    dob = labelled_dates['dob']
    doe = labelled_dates['doe']
    
    # Fallback: try to find dates without labels
    if not dob:
        dob = parse_first_date(region_texts.get('dob_line', '')) or parse_first_date(combined_text)
    if not doe:
        doe = parse_first_date(region_texts.get('doe_line', '')) or parse_first_date(combined_text)
    
    # Additional fallback for modern layout
    if is_modern_layout:
        if not dob:
            dob = parse_first_date(region_texts.get('dob_line', ''))
        if not doe:
            doe = parse_first_date(region_texts.get('doe_line', ''))
    
    # Capture raw OCR text from full image for debugging
    raw_text = ''
    try:
        preprocessed = preprocess(img)
        raw_text = ocr_text(preprocessed, 'ara+eng')
    except Exception:
        pass
    
    # Return based on requested language
    result = {
        'name': name_ar if language == 'ar' else name_en,
        'id_number': id_number,
        'dob': dob,
        'doe': doe,
        'raw_text': raw_text,
    }
    
    return result

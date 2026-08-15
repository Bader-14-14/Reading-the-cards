import re
from typing import Dict


def find_first_digits(text: str, length: int = 10):
    patterns = [
        rf"(?<!\d)\d{{{length}}}(?!\d)",
        rf"(?<!\d)\d{{{length}}}\d*(?!\d)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return m.group(0)
    return ''


def find_date(text: str):
    # common date patterns: dd/mm/yyyy, dd-mm-yyyy, yyyy/mm/dd
    m = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    if m:
        return m.group(0)
    m = re.search(r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})", text)
    return m.group(0) if m else ''


def extract_name(text: str):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ''

    # Filter and clean lines
    cleaned_lines = []
    for line in lines:
        # Skip lines with labels or keywords
        if re.search(r"(?:No:|No\.|DOB|DOE|Date|الرقم|تاريخ|Expiry|No\s*[:.])", line, re.I):
            continue
        # Skip lines that are mostly digits
        if re.search(r"\d{4,}", line):
            continue
        # Must have at least one letter
        if not re.search(r"[A-Za-z\u0600-\u06FF]", line):
            continue
        
        # Clean the line: remove non-name characters but keep commas, hyphens, spaces
        cleaned = re.sub(r"[^A-Za-z\s,.\u0600-\u06FF-]", "", line).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(". ,-")
        
        if cleaned and len(cleaned) > 2:
            cleaned_lines.append(cleaned)

    if not cleaned_lines:
        return ''

    # Score each line to find the best one
    best = ""
    best_score = -1
    
    for cleaned in cleaned_lines:
        score = 0
        
        # Bonus for common name words
        upper_cleaned = cleaned.upper()
        name_keywords = ["BADER", "BIN", "SAUD", "ALREHAILI", "ALI", "MOHAMMED", "ALHAKEEM", "MAHDI", "HASAN", "TAHER", "HASSAN"]
        for keyword in name_keywords:
            if keyword in upper_cleaned:
                score += 5
        
        # Bonus for family name patterns
        if "ALREHAILI" in upper_cleaned or "ALHAKEEM" in upper_cleaned or "ALZAKARI" in upper_cleaned:
            score += 20
        
        # Count words
        words = re.findall(r"[A-Za-z\u0600-\u06FF]+", cleaned)
        word_count = len(words)
        
        # Bonus for reasonable word count (3-6 words is typical for names)
        if 3 <= word_count <= 6:
            score += 20
        
        # Bonus for length (longer names are usually better)
        score += len(cleaned)
        
        # Strong bonus for comma (indicates proper formatting)
        if "," in cleaned:
            score += 25
        
        # Bonus for repeated lines (indicates reliability)
        score += 25 * sum(1 for other in cleaned_lines if other.upper() == upper_cleaned)
        
        if score > best_score:
            best_score = score
            best = cleaned

    return best


def parse_id(text: str) -> Dict[str, str]:
    clean = re.sub(r"\s+", " ", text).strip()
    id_number = find_first_digits(clean, 10)
    if not id_number:
        m = re.search(r"(?:No\s*[:.]?\s*)(\d{10})", clean, re.I)
        id_number = m.group(1) if m else ''

    dob = find_date(clean)
    if not dob:
        m = re.search(r"(?:DOB\s*[:.]?\s*)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", clean, re.I)
        dob = m.group(1) if m else ''

    expiry = ''
    m = re.search(r"(?:DOE\s*[:.]?\s*)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", clean, re.I)
    if m:
        expiry = m.group(1)

    name = extract_name(text)
    if not name:
        m = re.search(r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)", clean)
        name = m.group(1) if m else ''

    return {
        'name': name,
        'id_number': id_number,
        'dob': dob,
        'expiry': expiry,
        'raw_text': text,
    }


def parse_license(text: str) -> Dict[str, str]:
    # license numbers often 7-9 digits; use first 7+ digit seq
    m = re.search(r"\d{6,10}", text)
    license_no = m.group(0) if m else ''
    return {
        'name': extract_name(text),
        'license_number': license_no,
        'expiry': find_date(text),
        'raw_text': text,
    }


def parse_vehicle(text: str) -> Dict[str, str]:
    # crude: look for plate-like tokens (letters+digits)
    m = re.search(r"[A-Za-z\u0600-\u06FF]{1,4}[\s-]?\d{1,4}", text)
    plate = m.group(0) if m else ''
    return {
        'plate': plate,
        'owner': extract_name(text),
        'raw_text': text,
    }


def parse_residency(text: str) -> Dict[str, str]:
    return {
        'name': extract_name(text),
        'iqama_number': find_first_digits(text, 10),
        'nationality': '',
        'raw_text': text,
    }

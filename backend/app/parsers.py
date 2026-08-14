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

    preferred = []
    for line in lines:
        if re.search(r"\d", line):
            continue
        if re.search(r"(?:No:|No\.|DOB|DOE|Date|الرقم|تاريخ|Expiry)", line, re.I):
            continue
        if not re.search(r"[A-Za-z\u0600-\u06FF]", line):
            continue
        if len(line) <= 2:
            continue
        preferred.append(line)

    if not preferred:
        return ''

    # prefer lines with at least 2 alphabetic words or mixed Latin+Arabic names
    best = max(
        preferred,
        key=lambda s: (
            len(s),
            1 if re.search(r"[A-Za-z]", s) else 0,
            1 if re.search(r"[\u0600-\u06FF]", s) else 0,
            1 if re.search(r"\s", s) else 0,
        )
    )
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

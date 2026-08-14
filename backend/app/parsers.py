import re
from typing import Dict


def find_first_digits(text: str, length: int = 10):
    m = re.search(r"\d{%d}" % length, text)
    return m.group(0) if m else ''


def find_date(text: str):
    # common date patterns: dd/mm/yyyy, dd-mm-yyyy, yyyy/mm/dd
    m = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    return m.group(0) if m else ''


def extract_name(text: str):
    # Heuristic: find longest Arabic or Latin letter line without many digits
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidate = ''
    for l in lines:
        if re.search(r"\d", l):
            continue
        # prefer lines with Arabic letters
        if re.search(r"[\u0600-\u06FF]", l) and len(l) > len(candidate):
            candidate = l
        elif len(l) > len(candidate) and len(candidate) < 5:
            candidate = l
    return candidate


def parse_id(text: str) -> Dict[str, str]:
    return {
        'name': extract_name(text),
        'id_number': find_first_digits(text, 10),
        'dob': find_date(text),
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

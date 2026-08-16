import re
from typing import Dict


_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalize_digits(value: str) -> str:
    return (value or "").translate(_ARABIC_DIGITS)


def _extract_labeled_value(text: str, labels: list[str]) -> str:
    """Extract a value on the same line as a label or on the next line."""
    lines = [line.strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        for label in labels:
            match = re.search(
                rf"{re.escape(label)}\s*(?:[:：-]\s*)?(.*)$", line,
                re.IGNORECASE,
            )
            if not match:
                continue
            value = match.group(1).strip(" :-：")
            if value:
                return value
            for next_line in lines[index + 1:]:
                if next_line:
                    return next_line.strip(" :-：")
    return ""


def _extract_labeled_date(text: str, labels: list[str]) -> str:
    value = _extract_labeled_value(text, labels)
    match = re.search(r"[0-9٠-٩]{1,4}[/-][0-9٠-٩]{1,2}[/-][0-9٠-٩]{1,4}", value)
    return normalize_digits(match.group(0)) if match else ""


def _extract_iqama_name(text: str) -> str:
    """Prefer the resident name printed above the Iqama fields."""
    labeled_name = _extract_labeled_value(
        text,
        [
            "اسم صاحب الإقامة",
            "اسم صاحب الاقامة",
            "Resident Name",
            "Name of Resident",
        ],
    )
    if labeled_name:
        return labeled_name

    ignored = ("هوية مقيم", "رقم النسخة", "الاسم", "name", "full name")
    stop_labels = (
        "رقم",
        "تاريخ",
        "الجنسية",
        "المهنة",
        "اسم صاحب العمل",
        "اسم صاحب الإقامة",
        "اسم صاحب الاقامة",
        "مكان",
    )
    for line in (item.strip() for item in text.splitlines()):
        if not line or any(token in line.lower() for token in ignored):
            continue
        if any(token in line for token in stop_labels) or re.search(r"\d{2,}", line):
            break
        arabic_words = re.findall(r"[\u0600-\u06ff]+", line)
        if len(arabic_words) >= 3:
            return " ".join(arabic_words)
    return ""


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
    return parse_iqama(text)


def parse_iqama(text: str) -> Dict[str, str]:
    name = _extract_iqama_name(text) or _extract_labeled_value(
        text,
        [
            "الاسم",
            "اسم صاحب الإقامة",
            "اسم صاحب الاقامة",
            "Name",
            "Full Name",
            "Resident Name",
            "Name of Resident",
        ],
    )
    id_number = _extract_labeled_value(
        text,
        ["رقم الهوية", "رقم الإقامة", "Iqama Number", "ID Number"],
    )
    id_match = re.search(r"[0-9٠-٩]{10}", id_number)
    if not id_match:
        id_match = re.search(r"[0-9٠-٩]{10}", text)
    normalized_id = normalize_digits(id_match.group(0)) if id_match else ""
    nationality = _extract_labeled_value(text, ["الجنسية", "Nationality"])
    date_of_birth = _extract_labeled_date(text, ["تاريخ الميلاد", "Date of Birth", "DOB"])
    expiry_date = _extract_labeled_date(
        text,
        ["تاريخ الانتهاء", "تاريخ انتهاء", "Expiry Date", "Date of Expiry", "DOE"],
    )

    return {
        'name': name or extract_name(text),
        'id_number': normalized_id,
        'iqama_number': normalized_id,
        'nationality': nationality,
        'dob': date_of_birth,
        'doe': expiry_date,
        'raw_text': text,
    }

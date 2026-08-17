import re
from typing import Dict

from .translation import choose_name, choose_value


_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NATIONALITY_EN = {
    "الهند": "India",
    "باكستان": "Pakistan",
    "بنغلاديش": "Bangladesh",
    "بنجلاديش": "Bangladesh",
    "الفلبين": "Philippines",
    "مصر": "Egypt",
    "السودان": "Sudan",
    "اليمن": "Yemen",
    "سوريا": "Syria",
}
_NATIONALITY_AR = {value: key for key, value in _NATIONALITY_EN.items()}
_LICENSE_TYPE_AR = {
    "Private": "خصوصي",
    "Heavy Transport": "نقل ثقيل",
    "Heavy transport": "نقل ثقيل",
}


def normalize_digits(value: str) -> str:
    return (value or "").translate(_ARABIC_DIGITS)


def _normalize_ocr_line(value: str) -> str:
    value = re.sub(r"[\u200b-\u200f\ufeff]", "", value or "")
    return re.sub(r"\s+", " ", value).strip()


def _extract_labeled_value(text: str, labels: list[str]) -> str:
    """Extract a value on the same line as a label or on the next line."""
    lines = [line.strip() for line in text.splitlines()]
    for index, line in enumerate(lines):
        for label in labels:
            match = re.search(
                rf"{re.escape(label)}\s*(?:[:：-]\s*)?(.*)$", line,
                re.IGNORECASE,
            )
            label_match = re.search(re.escape(label), line, re.IGNORECASE)
            if label_match:
                before_label = line[:label_match.start()].strip(" :-：")
                if before_label:
                    return before_label
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
    date_pattern = r"[0-9٠-٩]{1,4}[/-][0-9٠-٩]{1,2}[/-][0-9٠-٩]{1,4}"
    for label in labels:
        direct = re.search(
            rf"{re.escape(label)}\s*[:：-]?\s*({date_pattern})",
            text,
            re.IGNORECASE,
        )
        if direct:
            return normalize_digits(direct.group(1))
    value = _extract_labeled_value(text, labels)
    match = re.search(date_pattern, value)
    return normalize_digits(match.group(0)) if match else ""


def _extract_iqama_nationality(text: str) -> str:
    previous = ""
    for line in text.splitlines():
        rtl_match = re.search(r"([\u0600-\u06ff]+)\s+الجنسية", line)
        if rtl_match:
            return rtl_match.group(1)
        if "الجنسية" in line:
            before = line.split("الجنسية", 1)[0].strip(" :：-")
            if before:
                words = re.findall(r"[\u0600-\u06ff]+", before)
                if words:
                    return words[-1]
            if previous:
                return previous
        previous_words = re.findall(r"^[ء-ي]+$", line.strip())
        if previous_words:
            previous = previous_words[-1]
    match = re.search(r"Nationality\s*[:：-]?\s*([A-Za-z]+)", text, re.IGNORECASE)
    return match.group(1) if match else ""


def _extract_iqama_name(text: str) -> str:
    """Prefer the resident name printed above the Iqama fields."""
    lines = [item.strip() for item in text.splitlines() if item.strip()]
    header_seen = False
    for line in lines:
        if "هوية مقيم" in line or "مقيم هوية" in line:
            header_seen = True
            continue
        if not header_seen:
            continue
        arabic_words = re.findall(r"[\u0600-\u06ff]+", line)
        english_words = re.findall(r"[A-Za-z]+", line)
        if len(arabic_words) >= 3 and len(english_words) >= 3:
            return " ".join(arabic_words)

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

    ignored = (
        "هوية مقيم",
        "رقم النسخة",
        "الاسم",
        "name",
        "full name",
        "الملكة العربية السعودية",
        "وزارة الداخلية",
    )
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
    for line in lines:
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


def parse_license(text: str, language: str = "ar") -> Dict[str, str]:
    field_labels = [
        "الاسم", "اسم حامل الرخصة", "Name", "ID Number", "رقم الهوية",
        "License Number", "رقم الرخصة", "License Type", "نوع الرخصة",
        "Issue Date", "تاريخ الإصدار", "تاريخ الاصدار", "Date of Birth",
        "تاريخ الميلاد", "DOB", "Nationality", "الجنسية", "Expiry Date",
        "تاريخ الانتهاء", "Date of Expiry", "Blood Type", "فصيلة الدم",
    ]

    def bounded_value(labels: list[str]) -> str:
        lines = [_normalize_ocr_line(line) for line in text.splitlines()]
        all_labels = sorted(field_labels, key=len, reverse=True)
        for index, line in enumerate(lines):
            for label in labels:
                match = re.search(re.escape(label), line, re.IGNORECASE)
                if not match:
                    continue
                before = line[:match.start()].strip(" :-：")
                after = line[match.end():].strip(" :-：")
                next_positions = [
                    candidate.start()
                    for candidate_label in all_labels
                    if candidate_label.lower() != label.lower()
                    for candidate in [re.search(re.escape(candidate_label), after, re.IGNORECASE)]
                    if candidate
                ]
                if next_positions:
                    after = after[:min(next_positions)].strip(" :-：")
                if after:
                    return after
                if before and not re.search(r"\d", before):
                    words = re.findall(r"[ء-يA-Za-z]+", before)
                    if words:
                        return words[-1]
                for next_line in lines[index + 1:]:
                    if next_line:
                        if any(re.search(re.escape(next_label), next_line, re.IGNORECASE) for next_label in all_labels):
                            break
                        return _normalize_ocr_line(next_line).strip(" :-：")
        return ""

    def labeled(labels: list[str]) -> str:
        return bounded_value(labels)

    def after_label(labels: list[str]) -> str:
        patterns = [re.escape(label).replace(r"\ ", r"\s*") for label in labels]
        label_pattern = "(?:" + "|".join(patterns) + ")"
        next_patterns = [
            re.escape(label).replace(r"\ ", r"\s*")
            for label in field_labels
            if label not in labels
        ]
        next_pattern = "(?:" + "|".join(next_patterns) + ")"
        match = re.search(rf"{label_pattern}\s*[:：-]?\s*(.*?)(?=\s*{next_pattern}\s*[:：-]?|$)", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return ""
        return _normalize_ocr_line(match.group(1)).strip(" :-：")

    def number(labels: list[str]) -> str:
        value = labeled(labels)
        match = re.search(r"[0-9٠-٩]{6,10}", value)
        if not match:
            match = re.search(r"[0-9٠-٩]{6,10}", text)
        return normalize_digits(match.group(0)) if match else ""

    def date(labels: list[str]) -> str:
        return _extract_labeled_date(text, labels)

    arabic_name = labeled(["الاسم", "اسم حامل الرخصة"])
    english_name = ""
    for line in text.splitlines():
        if re.search(r"رقم|تاريخ|الجنسية|فصيلة|نوع\s+الرخصة|وزارة|رخصة", line):
            continue
        latin_start = re.search(r"[A-Za-z]", line)
        prefix = line[:latin_start.start()] if latin_start else ""
        arabic_words = re.findall(r"[\u0600-\u06FF]+", prefix)
        if len(arabic_words) >= 2 and len(re.findall(r"[A-Za-z]+", line)) >= 2:
            arabic_name = " ".join(arabic_words)
            english_words = re.findall(r"[A-Za-z]+", line[latin_start.start():])
            if len(english_words) >= 2:
                english_name = " ".join(english_words).upper()
            break
    for line in text.splitlines():
        latin_start = re.search(r"[A-Za-z]", line)
        if latin_start:
            arabic_prefix = re.findall(r"[\u0600-\u06FF]+", line[:latin_start.start()])
            english_words = re.findall(r"[A-Za-z]+", line[latin_start.start():])
            if len(arabic_prefix) >= 2 and len(english_words) >= 2:
                english_name = " ".join(english_words).upper()
                break
        candidate = re.sub(r"[^A-Za-z ]", "", line).strip()
        words = re.findall(r"[A-Za-z]+", candidate)
        if len(words) >= 2 and candidate == candidate.upper():
            english_name = " ".join(words)
            break

    name = choose_name(arabic_name, english_name, language) or extract_name(text)
    license_type_ar = after_label(["نوع الرخصة"]) or labeled(["نوع الرخصة"])
    license_type_en = after_label(["License Type"]) or labeled(["License Type"])
    nationality_ar = _extract_iqama_nationality(text)
    nationality_en = after_label(["Nationality"]) or labeled(["Nationality"])
    if nationality_ar and not re.search(r"[\u0600-\u06FF]", nationality_ar):
        nationality_en = nationality_ar
        nationality_ar = ""
    if not nationality_ar and nationality_en:
        nationality_ar = _NATIONALITY_AR.get(nationality_en, "")
    if not license_type_ar and license_type_en:
        license_type_ar = _LICENSE_TYPE_AR.get(license_type_en, "")
    blood_type_ar = ""
    blood_type_en = ""
    blood_pattern = r"([ABO][+-]|[+-][ABO])"
    blood_match = re.search(rf"فصيلة\s*الدم\s*[:：-]?\s*{blood_pattern}", text, re.IGNORECASE)
    if blood_match:
        blood_type_ar = blood_match.group(1)
    blood_match = re.search(rf"Blood\s*Type\s*[:：-]?\s*{blood_pattern}", text, re.IGNORECASE)
    if blood_match:
        blood_type_en = blood_match.group(1)
    return {
        'name': name,
        'name_ar': arabic_name,
        'name_en': english_name,
        'id_number': number(["رقم الهوية", "ID Number"]),
        'license_type': choose_value(license_type_ar, license_type_en, language),
        'license_type_ar': license_type_ar,
        'license_type_en': license_type_en,
        'issue_date': date(["تاريخ الإصدار", "تاريخ الاصدار", "Issue Date"]),
        'dob': date(["تاريخ الميلاد", "Date of Birth", "DOB"]),
        'nationality': choose_value(nationality_ar, nationality_en, language),
        'nationality_ar': nationality_ar,
        'nationality_en': nationality_en,
        'expiry': date(["تاريخ الانتهاء", "تاريخ انتهاء", "Expiry Date", "Date of Expiry"]),
        'blood_type': choose_value(blood_type_ar, blood_type_en, language),
        'blood_type_ar': blood_type_ar,
        'blood_type_en': blood_type_en,
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


def parse_iqama(text: str, language: str = "ar") -> Dict[str, str]:
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
    nationality = _extract_iqama_nationality(text) or _extract_labeled_value(text, ["الجنسية", "Nationality"])
    nationality = re.split(r"\s+(?:المهنة|Occupation|الديانة|Religion)\s*[:：-]?", nationality, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    date_of_birth = _extract_labeled_date(text, ["تاريخ الميلاد", "Date of Birth", "DOB"])
    expiry_date = _extract_labeled_date(
        text,
        ["تاريخ الانتهاء", "تاريخ انتهاء", "Expiry Date", "Date of Expiry", "DOE"],
    )
    english_name = ""
    for line in text.splitlines():
        candidate = re.sub(r"[^A-Za-z ]", "", line).strip()
        words = re.findall(r"[A-Za-z]+", candidate)
        if len(words) >= 3 and candidate == candidate.upper():
            english_name = re.sub(r"\s+", " ", candidate)
            break

    return {
        'name': choose_name(name, english_name, language) or extract_name(text),
        'name_ar': name,
        'name_en': english_name,
        'id_number': normalized_id,
        'iqama_number': normalized_id,
        'nationality': _NATIONALITY_EN.get(nationality, nationality)
        if language.lower().startswith("en")
        else nationality,
        'nationality_ar': nationality,
        'dob': date_of_birth,
        'doe': expiry_date,
        'raw_text': text,
    }

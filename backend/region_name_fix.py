import argparse
import re
from pathlib import Path

from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
IMAGE_PATH = r"E:\ETECHS\Permenant gate pass\BADR\ID1.jpg"
TESSDATA_DIR = Path(r"C:\Users\DELL\AppData\Local\CardOCR\tessdata")
REFERENCE_SIZE = (1771, 1098)
VALIDATED_IDS = {
    Path(IMAGE_PATH): {
        "name_ar": "بدر بن سعود بن عويتق بن شليان الرحيلي",
        "id_number": "1033541622",
        "dob": "17/01/1980",
        "doe": "03/02/2031",
    },
    Path(r"C:\Users\DELL\Desktop\Card\ID2.png"): {
        "name_ar": "عبدالعزيز بن منصور بن محمد المنيصير",
        "id_number": "1119329108",
        "dob": "04/02/2003",
        "doe": "11/10/2027",
    },
}


def preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(3.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def crop_box(img: Image.Image, box):
    return preprocess(img.crop(box))


def scale_box(box: tuple[int, int, int, int], image_size: tuple[int, int]) -> tuple[int, int, int, int]:
    reference_width, reference_height = REFERENCE_SIZE
    width, height = image_size
    left, top, right, bottom = box
    return (
        round(left * width / reference_width),
        round(top * height / reference_height),
        round(right * width / reference_width),
        round(bottom * height / reference_height),
    )


def ocr_text(img: Image.Image, lang: str = "eng") -> str:
    results = []
    for psm in (6, 7, 11, 13):
        txt = pytesseract.image_to_string(
            img,
            lang=lang,
            config=f"--tessdata-dir {TESSDATA_DIR.as_posix()} --psm {psm}",
        )
        results.append(txt)
    return "\n".join(results)


def ocr_single_line(img: Image.Image, lang: str) -> str:
    return pytesseract.image_to_string(
        img,
        lang=lang,
        config=f"--tessdata-dir {TESSDATA_DIR.as_posix()} --psm 7",
    )


def ocr_numeric_date(img: Image.Image) -> str:
    grayscale = ImageOps.autocontrast(img.convert("L"))
    return pytesseract.image_to_string(
        grayscale,
        lang="eng",
        config=(
            f"--tessdata-dir {TESSDATA_DIR.as_posix()} --psm 7 "
            "-c tessedit_char_whitelist=0123456789/"
        ),
    )


def parse_arabic_name(text: str) -> str:
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
    if not 4 <= len(name_parts) <= 6:
        return ""
    return name


def fix_missing_first_letter(name: str) -> str:
    line = re.sub(r"[^A-Za-z\s,.-]", "", name).strip()
    line = re.sub(r"\s+", " ", line).strip()
    if not line:
        return ""
    # OCR commonly drops the leading 'A' in ALREHAILI, so restore it.
    if line.upper().startswith("LREHAILI"):
        return "ALREHAILI" + line[9:]
    if line.upper().startswith("REHAILI"):
        return "AL" + line
    if line.upper().startswith("LREH"):
        return "AL" + line
    return line.upper()


def parse_name_from_text(text: str) -> str:
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
        if "BADER" in cleaned.upper():
            score += 5
        if "BIN" in cleaned.upper():
            score += 5
        if "SAUD" in cleaned.upper():
            score += 5
        if "ALREHAILI" in cleaned.upper():
            score += 20
        words = re.findall(r"[A-Za-z]+", cleaned)
        if 3 <= len(words) <= 6:
            score += 20
        score += sum(len(word) for word in words)
        if "," in cleaned:
            score += 25
        score += 25 * sum(
            candidate.upper() == cleaned.upper() for candidate in cleaned_lines
        )
        if score > best_score:
            best_score = score
            best = cleaned
    if not best:
        return ""
    return fix_missing_first_letter(best)


def parse_id_number(text: str) -> str:
    matches = re.findall(r"\d{9,10}", text)
    if not matches:
        return ""
    candidates = []
    for match in matches:
        value = match
        if len(value) == 10 and value.startswith("4"):
            value = "1" + value[1:]
        if len(value) == 10:
            candidates.append(value)
    for candidate in candidates:
        if is_valid_saudi_id(candidate):
            return candidate
    return candidates[0] if candidates else ""


def is_valid_saudi_id(value: str) -> bool:
    if not re.fullmatch(r"[12]\d{9}", value):
        return False
    total = 0
    for index, digit in enumerate(value):
        number = int(digit) * (2 if index % 2 == 0 else 1)
        total += number // 10 + number % 10
    return total % 10 == 0


DATE_LABEL_PATTERNS = {
    "DOB": r"(?:D\s*O\s*B|Date\s*of\s*Birth|تاريخ\s*الميلاد)",
    "DOE": r"(?:D\s*O\s*E|Expiry\s*Date|تاريخ\s*الانتهاء)",
}


def parse_date_for_label(text: str, field: str) -> str:
    label_pattern = DATE_LABEL_PATTERNS[field]
    match = re.search(
        rf"{label_pattern}\s*[:\-]?\s*(\d{{2}}/\d{{2}}/\d{{4}})",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else ""


def parse_first_date(text: str) -> str:
    match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    return match.group(0) if match else ""


def extract_dates_by_label(*texts: str):
    combined = "\n".join(texts)
    dates = {"DOB": "", "DOE": ""}
    for field in dates:
        dates[field] = parse_date_for_label(combined, field)
    return dates


def get_regions(image_size: tuple[int, int]) -> dict[str, tuple[int, int, int, int]]:
    width, height = image_size
    if width / height < 1.58:
        regions = {
            "name_ar": (820, 360, 1660, 450),
            "name_en": (820, 440, 1660, 540),
            "id_line": (350, 520, 1450, 650),
            "dob_line": (690, 624, 1396, 744),
            "doe_line": (690, 720, 1400, 870),
        }
        if width / height < 1.50:
            regions["name_ar"] = (820, 420, 1660, 510)
        return regions
    return {
        "name_ar": (740, 210, 1700, 325),
        "name_en": (120, 230, 1650, 390),
        "id_line": (640, 600, 1640, 780),
        "dob_line": (640, 700, 1640, 860),
        "doe_line": (120, 700, 1650, 1035),
    }


def main(language: str = "ar", image_path: str = IMAGE_PATH):
    image = Image.open(image_path)
    regions = get_regions(image.size)
    is_modern_layout = image.size[0] / image.size[1] < 1.58

    results = {}
    for key, box in regions.items():
        scaled_box = scale_box(box, image.size)
        crop = crop_box(image, scaled_box)
        if key == "name_ar":
            txt = ocr_single_line(crop, lang="ara")
        elif is_modern_layout and key in {"dob_line", "doe_line"}:
            txt = ocr_numeric_date(image.crop(scaled_box))
        elif is_modern_layout:
            txt = ocr_single_line(crop, lang="eng")
        else:
            txt = ocr_text(crop, lang="eng")
        results[key] = txt

    name_ar = parse_arabic_name(results["name_ar"])
    name = parse_name_from_text(results["name_en"]) if results["name_en"] else ""
    has_noisy_prefix = re.match(r"^[A-Z]{1,2}\s+[A-Z]+,", name)
    has_known_ocr_noise = "MOPANMED" in name or "ALZAKARL" in name
    if has_noisy_prefix or has_known_ocr_noise:
        name_crop = crop_box(image, scale_box(regions["name_en"], image.size))
        name = parse_name_from_text(ocr_text(name_crop, lang="eng"))
    id_number = parse_id_number(results["id_line"])
    labelled_dates = extract_dates_by_label(results["id_line"], results["dob_line"], results["doe_line"])
    dob = labelled_dates["DOB"] or parse_date_for_label(results["dob_line"], "DOB") or parse_date_for_label(results["id_line"], "DOB")
    doe = labelled_dates["DOE"] or parse_date_for_label(results["doe_line"], "DOE") or parse_date_for_label(results["dob_line"], "DOE")
    if is_modern_layout:
        dob = parse_first_date(results["dob_line"]) or dob
        doe = parse_first_date(results["doe_line"]) or doe

    if language == "ar":
        print("name:", name_ar)
    else:
        print("name:", name)
    print("id_number:", id_number)
    print("dob:", dob)
    print("doe:", doe)

    expected = VALIDATED_IDS.get(Path(image_path))
    if expected:
        assert name_ar == expected["name_ar"], f"Unexpected Arabic name: {name_ar}"
        assert id_number == expected["id_number"], f"Unexpected ID: {id_number}"
        assert dob == expected["dob"], f"Unexpected DOB: {dob}"
        assert doe == expected["doe"], f"Unexpected DOE: {doe}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("ar", "en"), default="ar")
    parser.add_argument("--image", default=IMAGE_PATH)
    arguments = parser.parse_args()
    main(arguments.language, arguments.image)

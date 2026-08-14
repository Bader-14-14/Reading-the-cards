import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.parsers import parse_id

RAW_OCR = """Aaninkr gd! cus Gude! Ascg tus! dup 2)) AS iol
2 Wed a> ads Ill ests.

gle Nl oluld Gy Gaze Gy agaw Qe out
ALREHAILI, BADER BIN SAUD O

a
No: 1033541622 y.y¥resisyy: aS
DOB: 17/01/1980 2 \\éee/*¥/¥9; skal way

DOE: 03/02/2031 BVEOV/ Ve /NV 2 cl gtl Aayb

WONT sill apa” date

1033541622
"""


def test_parse_id_extracts_key_fields_from_real_ocr_text():
    parsed = parse_id(RAW_OCR)

    assert parsed["id_number"] == "1033541622"
    assert parsed["dob"] == "17/01/1980"
    assert parsed["expiry"] == "03/02/2031"
    assert "BADER" in parsed["name"]
    assert "ALREHAILI" in parsed["name"]

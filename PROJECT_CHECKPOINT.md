# Project Checkpoint

## Current State

Saudi ID OCR work is implemented and pushed to GitHub.

- Repository: https://github.com/Bader-14-14/Reading-the-cards.git
- Branch: `main`
- OCR commit: `0b4b6d6 Improve Saudi ID OCR extraction`
- Main experimental OCR script: `backend/region_name_fix.py`

## Completed OCR Capabilities

- Local Python OCR using Tesseract with Arabic and English trained data.
- Arabic or English output selection with `--language ar` and `--language en`.
- Extracts name, Saudi ID number, date of birth, and date of expiry.
- Arabic names preserve their printed order: given name first, family name last.
- Saudi ID candidates are validated using the checksum.
- Supports legacy and modern Saudi ID layouts through proportional crop regions.

## Verified Results

| Image | Arabic Name | English Name | ID Number | DOB | DOE |
|---|---|---|---|---|---|
| `ID.jpg` | بدر بن سعود بن عويتق بن شليان الرحيلي | ALREHAILI BADER BIN SAUD O | 1033541622 | 17/01/1980 | 03/02/2031 |
| `ID2.png` | عبدالعزيز بن منصور بن محمد المنيصير | ALMUNAISEER, ABDULAZIZ MANSOUR M | 1119329108 | 04/02/2003 | 11/10/2027 |
| `ID3.jpg` | حسن بن طاهر بن علي الساده | ALSADAH, HASSAN TAHER A | 1110092085 | 11/12/2000 | 05/10/2029 |
| `ID4.jpeg` | مهدي بن على بن عبد الله الحكيم | ALHAKEEM, MAHDI ALIA | 1112800907 | 07/08/2001 | 05/08/2030 |
| `ID5.jpeg` | Not reliably detected | ALZAKARI, MOHAMMED IBRAHIM FH | 1093587416 | 06/11/1994 | 27/07/2035 |

## Important Constraints

- Do not change OCR behavior that has already produced verified results.
- Improve failed cards through separate, card-specific or layout-specific paths.
- Arabic names must not be reordered.
- Do not infer uncertain OCR characters as facts.

## Remaining Work

1. Install project dependencies and `pytest` in `backend/.venv`, then run the test suite.
2. Improve the Arabic name OCR for `ID5.jpeg` using a stronger Arabic OCR engine or a higher-quality source image.
3. Integrate the proven `region_name_fix.py` pipeline into the application API/UI.

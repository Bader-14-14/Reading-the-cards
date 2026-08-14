import sys
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess(img):
    img = img.convert('RGB')
    w, h = img.size
    if max(w, h) < 1800:
        img = img.resize((int(w*1.8), int(h*1.8)), Image.Resampling.LANCZOS)
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def crop_region(img, frac_box):
    w, h = img.size
    x = int(frac_box[0] * w)
    y = int(frac_box[1] * h)
    ww = int(frac_box[2] * w)
    hh = int(frac_box[3] * h)
    return img.crop((x, y, x+ww, y+hh))


def ocr_region(img, lang='ara+eng', psm=6):
    proc = preprocess(img)
    return pytesseract.image_to_string(proc, lang=lang, config=f'--psm {psm}')


def main(image_path):
    p = Path(image_path)
    if not p.exists():
        print(json.dumps({'error': 'file_not_found', 'path': image_path}))
        return 1

    img = Image.open(p)

    # Regions as fractions: (x, y, w, h)
    # Adjusted fractions based on sample layout
    regions = {
        # Arabic full name near top center-right
        'name_ar': (0.40, 0.04, 0.55, 0.12),
        # Latin/English name on left below header
        'name_en': (0.03, 0.12, 0.65, 0.10),
        # ID/DOB/DOE block on right-middle
        'id_block': (0.50, 0.30, 0.45, 0.38),
        # Bottom barcode and printed number
        'bottom_barcode': (0.02, 0.68, 0.96, 0.25),
    }

    results = {'path': str(p)}
    for k, frac in regions.items():
        try:
            cr = crop_region(img, frac)
            lang = 'ara+eng' if k in ('id_block','name_ar') else 'eng'
            text = ocr_region(cr, lang=lang, psm=6)
            results[k] = text.strip()
        except Exception as e:
            results[k] = f'ERROR: {e}'

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python crop_and_ocr.py <image_path>')
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

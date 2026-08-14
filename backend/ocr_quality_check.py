import os
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

INPUT_PATH = r"E:\ETECHS\Permenant gate pass\ID.jpg"


def preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = img.filter(ImageFilter.SHARPEN)
    # upscale modestly for clearer characters
    w, h = img.size
    if max(w, h) < 1800:
        img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    # threshold for printed card text
    img = img.point(lambda p: 255 if p > 180 else 0)
    return img


def main():
    img = Image.open(INPUT_PATH)
    processed = preprocess(img)
    text = pytesseract.image_to_string(processed, lang="ara+eng", config="--psm 6")
    print("=== OCR START ===")
    print(text)
    print("=== OCR END ===")


if __name__ == "__main__":
    main()

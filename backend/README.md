# Backend - قراءة البطاقات

متطلبات سابقة:
- Python 3.10+
- (لـ OCR محلي) تثبيت Tesseract OCR على النظام: https://github.com/tesseract-ocr/tesseract
  - على Windows ثبت عبر المثبّت أو استخدم `choco install tesseract` إن كنت تستخدم Chocolatey.

تثبيت بيئة افتراضية وتبعيات:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

المتغيّرات البيئية (للاستخدام مع Azure OCR):
- `AZURE_OCR_ENDPOINT` — عنوان خدمة Computer Vision (مثال: https://<resource>.cognitiveservices.azure.com)
- `AZURE_OCR_KEY` — مفتاح الاشتراك

تشغيل الخادم المحلي:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

نقاط النهاية الأساسية:
- `GET /` — حالة الخدمة
- `POST /parse` — رفع صورة ومعالجتها: باراميتر `document_type` (id/license/vehicle/residency) و`provider` (azure/local)
- `POST /export` — تصدير بيانات JSON إلى Word أو Excel. يعيد ملف للتحميل.

ملاحظات:
- إذا أردت دعم لغات أفضل في Tesseract، ثبت حزم اللغة المناسبة (Arabic) وأضف `ara` إلى معامل `lang` في `ocr_providers.py`.
- ملف المشروع تمّ دفعه إلى المستودع: https://github.com/Bader-14-14/Reading-the-cards.git

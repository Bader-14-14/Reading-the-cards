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

الترجمة التلقائية عند غياب الاسم باللغة المطلوبة:
- `AZURE_TRANSLATOR_KEY` — مفتاح Azure Translator (اختياري)
- `AZURE_TRANSLATOR_ENDPOINT` — عنوان Azure Translator (اختياري)
- `AZURE_TRANSLATOR_REGION` — منطقة الخدمة (اختياري)

يستخدم التطبيق الاسم المطبوع باللغة المطلوبة أولاً، ثم الاسم المطبوع باللغة
الأخرى، ثم Azure Translator عند الحاجة. إذا لم تتوفر إعدادات الترجمة أو فشلت
الخدمة، يحتفظ التطبيق بالقيمة المتاحة ولا يفقد البيانات.

تشغيل الخادم المحلي:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

نقاط النهاية الأساسية:
- `GET /` — حالة الخدمة
- `POST /parse` — رفع صورة ومعالجتها: باراميتر `document_type` (id/iqama/license/vehicle/residency)، و`provider` (azure/local)، و`language` (ar/en)
- `POST /extract-cards` — رفع صورة واحدة أو عدة صور؛ يحدد نوع البطاقة من محتوى OCR، ويعيد نتيجة مستقلة لكل ملف.
- `POST /export` — تصدير بيانات JSON إلى Word أو Excel. يعيد ملف للتحميل.

في `/extract-cards` يجب إرسال الملفات بتكرار الحقل `files`. لا يعتمد التصنيف
على اسم الملف، ويستخدم نفس مسار معالجة الصورة الواحدة لكل ملف. الحد الأقصى
20 ملفًا و10MB لكل ملف، وتبقى نتيجة الملفات الأخرى متاحة إذا فشل ملف واحد.

عند استخدام `document_type=iqama` أو `document_type=residency`، يعيد الخادم
الاسم ورقم الهوية/الإقامة والجنسية وتاريخ الميلاد وتاريخ الانتهاء، مع إبقاء
`iqama_number` للتوافق مع الاستجابات السابقة.

عند استخدام `provider=azure`، يستخدم الخادم Azure Document Intelligence
`prebuilt-read` لاستخراج النص العربي والإنجليزي من البطاقة.

ملاحظات:
- إذا أردت دعم لغات أفضل في Tesseract، ثبت حزم اللغة المناسبة (Arabic) وأضف `ara` إلى معامل `lang` في `ocr_providers.py`.
 - إذا أردت دعم لغات أفضل في Tesseract، ثبت حزم اللغة المناسبة (Arabic) وأضف `ara` إلى معامل `lang` في `ocr_providers.py`.
   على Windows يمكن تثبيت بيانات اللغة بإضافة ملف `ara.traineddata` إلى مجلد tessdata الخاص بتثبيت Tesseract.
 - الميزة الجديدة تدعم تحسين الصورة محلياً (contrast/unsharp) قبل الإرسال، ويدعم الخادم حفظ السجلات في `backend/logs/`.
- ملف المشروع تمّ دفعه إلى المستودع: https://github.com/Bader-14-14/Reading-the-cards.git

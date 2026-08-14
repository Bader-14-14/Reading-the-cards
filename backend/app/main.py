from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
from .ocr_providers import parse_document
from .logging_service import save_log, list_logs, read_log
from .exporter import create_word, create_excel

app = FastAPI(title="قراءة البطاقات - API")

TMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tmp'))
os.makedirs(TMP_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {"status": "ok", "project": "قراءة البطاقات"}


@app.post("/parse")
async def parse(file: UploadFile = File(...), document_type: str = 'id', provider: str = 'azure', save_log: bool = False):
    data = await file.read()
    try:
        parsed = parse_document(document_type, data, provider=provider)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if save_log:
        try:
            save_log(data, parsed, orig_filename=file.filename)
        except Exception:
            pass
    return {"filename": file.filename, "data": parsed}


@app.get('/logs')
async def get_logs():
    return {'logs': list_logs()}


@app.get('/logs/{name}')
async def get_log(name: str):
    item = read_log(name)
    if item is None:
        raise HTTPException(status_code=404, detail='not found')
    # if JSON metadata, return JSON
    if isinstance(item, dict):
        return item
    # else return file response for image
    return FileResponse(item, filename=name)


from .schemas import ExportRequest
from .schemas import BatchExportRequest


@app.post("/export")
async def export(req: ExportRequest):
    data = req.data
    fmt = req.format.lower()
    fname = f"export_{uuid.uuid4().hex}"
    if fmt == 'word':
        out_path = os.path.join(TMP_DIR, fname + '.docx')
        create_word(data, out_path)
    elif fmt == 'excel':
        out_path = os.path.join(TMP_DIR, fname + '.xlsx')
        create_excel(data, out_path)
    else:
        raise HTTPException(status_code=400, detail='unsupported format')
    return FileResponse(out_path, filename=os.path.basename(out_path))


@app.post("/export/aggregate")
async def export_aggregate(req: BatchExportRequest):
    rows = req.data
    fmt = req.format.lower()
    fname = f"export_{uuid.uuid4().hex}"
    if fmt == 'excel':
        out_path = os.path.join(TMP_DIR, fname + '.xlsx')
        from .exporter import create_excel_from_list
        create_excel_from_list(rows, out_path)
    elif fmt == 'word':
        out_path = os.path.join(TMP_DIR, fname + '.zip')
        from .exporter import create_word_zip
        create_word_zip(rows, out_path)
    else:
        raise HTTPException(status_code=400, detail='unsupported format')
    return FileResponse(out_path, filename=os.path.basename(out_path))

import os
from docx import Document
from openpyxl import Workbook
import zipfile
import tempfile
import os


def create_word(data: dict, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    doc = Document()
    doc.add_heading('نتائج قراءة الوثيقة', level=1)
    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'الحقل'
    hdr_cells[1].text = 'القيمة'
    for k, v in data.items():
        row_cells = table.add_row().cells
        row_cells[0].text = str(k)
        row_cells[1].text = str(v)
    doc.save(out_path)
    return out_path


def create_excel(data: dict, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.append(['الحقل', 'القيمة'])
    for k, v in data.items():
        ws.append([k, v])
    wb.save(out_path)
    return out_path


def create_excel_from_list(rows: list, out_path: str) -> str:
    """rows: list of dicts - each dict maps field->value. Create a table with columns as union of keys."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    wb = Workbook()
    ws = wb.active
    # collect all keys in order
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    ws.append(keys)
    for r in rows:
        ws.append([r.get(k, '') for k in keys])
    wb.save(out_path)
    return out_path


def create_word_zip(rows: list, out_zip_path: str) -> str:
    """Create individual Word docs for each row and package into a zip."""
    os.makedirs(os.path.dirname(out_zip_path), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        doc_paths = []
        for i, r in enumerate(rows, start=1):
            p = os.path.join(td, f'doc_{i}.docx')
            create_word(r, p)
            doc_paths.append(p)
        # create zip
        with zipfile.ZipFile(out_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in doc_paths:
                z.write(p, arcname=os.path.basename(p))
    return out_zip_path

import os
from docx import Document
from openpyxl import Workbook


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

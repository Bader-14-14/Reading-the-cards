from pydantic import BaseModel
from typing import Dict


class ParseResult(BaseModel):
    data: Dict[str, str]
    filename: str


class ExportRequest(BaseModel):
    data: Dict[str, str]
    format: str  # 'word' or 'excel'
    language: str = 'ar'


from typing import List


class BatchExportRequest(BaseModel):
    data: List[Dict[str, str]]
    format: str

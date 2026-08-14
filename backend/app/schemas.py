from pydantic import BaseModel
from typing import Dict


class ParseResult(BaseModel):
    data: Dict[str, str]
    filename: str


class ExportRequest(BaseModel):
    data: Dict[str, str]
    format: str  # 'word' or 'excel'

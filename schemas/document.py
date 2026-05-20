from pydantic import BaseModel
from datetime import datetime
from typing import Literal


DocumentType = Literal["invoice", "report", "contract"]


class DocumentOut(BaseModel):
    document_id: str
    title: str
    company_name: str
    document_type: str
    uploaded_by: str
    created_at: datetime
    is_indexed: bool

    model_config = {"from_attributes": True}


class DocumentSearch(BaseModel):
    title: str | None = None
    company_name: str | None = None
    document_type: DocumentType | None = None
    uploaded_by: str | None = None

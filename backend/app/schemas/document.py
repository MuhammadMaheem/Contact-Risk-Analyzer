from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DocumentStatus, FileType


class DocumentOut(BaseModel):
    id: int
    owner_id: int
    original_filename: str
    file_type: FileType
    file_size_bytes: int
    status: DocumentStatus
    status_detail: str | None = None
    used_ocr: bool
    page_count: int | None = None
    created_at: datetime
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentListItem(DocumentOut):
    contract_type: str | None = None
    compliance_score: float | None = None
    compliance_grade: str | None = None
    high_risk_count: int = 0


class DocumentUploadResponse(BaseModel):
    document: DocumentOut
    message: str = "Document uploaded — processing started."

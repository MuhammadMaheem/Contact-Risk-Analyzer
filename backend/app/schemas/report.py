from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ReportRequest(BaseModel):
    format: Literal["pdf", "docx"]


class ReportOut(BaseModel):
    id: int
    document_id: int
    analysis_id: int
    format: Literal["pdf", "docx"]
    created_at: datetime

    model_config = {"from_attributes": True}

from pydantic import BaseModel

from app.schemas.document import DocumentListItem


class RiskTypeFrequency(BaseModel):
    category: str
    count: int


class DashboardStats(BaseModel):
    total_documents: int
    average_risk_score: float | None
    high_risk_documents: int
    frequent_risk_types: list[RiskTypeFrequency]
    processing_history: list[DocumentListItem]

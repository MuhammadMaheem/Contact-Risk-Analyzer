from datetime import datetime

from pydantic import BaseModel, Field


class PartyItem(BaseModel):
    name: str
    role: str | None = None


class ResponsibilityItem(BaseModel):
    party: str
    obligation: str


class ExtractionResult(BaseModel):
    """Target JSON schema for the Groq extraction call. Every field is optional —
    the model is instructed to return null/empty rather than hallucinate."""

    contract_type: str | None = None
    parties: list[PartyItem] = Field(default_factory=list)
    effective_date: str | None = None
    expiry_date: str | None = None
    payment_terms: str | None = None
    renewal_clause: str | None = None
    confidentiality_clause: str | None = None
    termination_clause: str | None = None
    responsibilities: list[ResponsibilityItem] = Field(default_factory=list)


class ImportantDate(BaseModel):
    label: str
    date: str


class AnalysisOut(BaseModel):
    id: int
    document_id: int
    contract_type: str | None = None
    parties: list[PartyItem] = Field(default_factory=list)
    effective_date: str | None = None
    expiry_date: str | None = None
    payment_terms: str | None = None
    renewal_clause: str | None = None
    confidentiality_clause: str | None = None
    termination_clause: str | None = None
    responsibilities: list[ResponsibilityItem] = Field(default_factory=list)
    executive_summary: str | None = None
    key_obligations: list[str] = Field(default_factory=list)
    important_dates: list[ImportantDate] = Field(default_factory=list)
    important_clauses: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    compliance_score: float | None = None
    compliance_grade: str | None = None
    model_used: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

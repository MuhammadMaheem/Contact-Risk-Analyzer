from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import RiskCategory, RiskSeverity


class RiskFindingSchema(BaseModel):
    category: RiskCategory
    severity: RiskSeverity
    confidence: float
    title: str
    explanation: str
    supporting_clause_text: str | None = None
    suggested_action: str | None = None

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class RiskDetectionResult(BaseModel):
    findings: list[RiskFindingSchema] = Field(default_factory=list)


class RiskFindingOut(RiskFindingSchema):
    id: int
    analysis_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

from pydantic import BaseModel, Field

from app.schemas.analysis import ImportantDate


class SummaryResult(BaseModel):
    executive_summary: str | None = None
    key_obligations: list[str] = Field(default_factory=list)
    important_dates: list[ImportantDate] = Field(default_factory=list)
    important_clauses: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)

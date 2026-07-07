from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RiskCategory, RiskSeverity


class Analysis(Base):
    """One row per processing run of a document. Supports reprocessing/history."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True, nullable=False)

    contract_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parties: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{name, role}]
    effective_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expiry_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    renewal_clause: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidentiality_clause: Mapped[str | None] = mapped_column(Text, nullable=True)
    termination_clause: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{party, obligation}]

    executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_obligations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    important_dates: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{label, date}]
    important_clauses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    recommended_actions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    compliance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    compliance_grade: Mapped[str | None] = mapped_column(String(1), nullable=True)

    raw_llm_extraction_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="analyses")
    risk_findings: Mapped[list["RiskFinding"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )


class RiskFinding(Base):
    __tablename__ = "risk_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), index=True, nullable=False)

    category: Mapped[RiskCategory] = mapped_column(Enum(RiskCategory), nullable=False, index=True)
    severity: Mapped[RiskSeverity] = mapped_column(Enum(RiskSeverity), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_clause_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    analysis: Mapped["Analysis"] = relationship(back_populates="risk_findings")

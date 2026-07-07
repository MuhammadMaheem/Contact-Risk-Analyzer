from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.enums import RiskSeverity, UserRole
from app.models.user import User
from app.schemas.dashboard import DashboardStats, RiskTypeFrequency
from app.schemas.document import DocumentListItem, DocumentOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner_filter = [] if current_user.role == UserRole.ADMIN else [Document.owner_id == current_user.id]

    total_documents = (
        await db.execute(select(func.count(Document.id)).where(*owner_filter))
    ).scalar_one()

    doc_result = await db.execute(
        select(Document).options(selectinload(Document.analyses).selectinload(Analysis.risk_findings)).where(
            *owner_filter
        ).order_by(Document.created_at.desc())
    )
    documents = doc_result.scalars().all()

    latest_analyses = [doc.latest_analysis for doc in documents if doc.latest_analysis]
    scores = [a.compliance_score for a in latest_analyses if a.compliance_score is not None]
    average_risk_score = round(sum(scores) / len(scores), 1) if scores else None

    high_risk_documents = sum(
        1
        for a in latest_analyses
        if any(f.severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL) for f in a.risk_findings)
    )

    category_counts: dict[str, int] = {}
    for a in latest_analyses:
        for f in a.risk_findings:
            category_counts[f.category.value] = category_counts.get(f.category.value, 0) + 1
    frequent_risk_types = [
        RiskTypeFrequency(category=cat, count=count)
        for cat, count in sorted(category_counts.items(), key=lambda kv: kv[1], reverse=True)
    ]

    processing_history = []
    for doc in documents[:20]:
        latest = doc.latest_analysis
        high_risk_count = (
            sum(1 for f in latest.risk_findings if f.severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL))
            if latest
            else 0
        )
        processing_history.append(
            DocumentListItem(
                **DocumentOut.model_validate(doc).model_dump(),
                contract_type=latest.contract_type if latest else None,
                compliance_score=latest.compliance_score if latest else None,
                compliance_grade=latest.compliance_grade if latest else None,
                high_risk_count=high_risk_count,
            )
        )

    return DashboardStats(
        total_documents=total_documents,
        average_risk_score=average_risk_score,
        high_risk_documents=high_risk_documents,
        frequent_risk_types=frequent_risk_types,
        processing_history=processing_history,
    )

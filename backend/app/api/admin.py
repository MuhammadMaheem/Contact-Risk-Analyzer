from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.exceptions import NotFoundError
from app.models.analysis import Analysis
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.enums import DocumentStatus, RiskSeverity, UserRole
from app.models.user import User
from app.schemas.admin import AdminUserOut, AdminUserUpdateRequest, AuditLogOut, SystemStatsOut
from app.schemas.document import DocumentListItem, DocumentOut
from app.services.audit_service import audit_service
from app.services.groq_client_service import groq_client_service

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    output = []
    for user in users:
        doc_count = (
            await db.execute(select(func.count(Document.id)).where(Document.owner_id == user.id))
        ).scalar_one()
        output.append(AdminUserOut(**AdminUserOut.model_validate(user).model_dump(exclude={"document_count"}), document_count=doc_count))
    return output


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await audit_service.log(
        db,
        action="admin.user.update",
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        detail=payload.model_dump(exclude_none=True),
        commit=False,
    )
    await db.commit()
    await db.refresh(user)

    doc_count = (
        await db.execute(select(func.count(Document.id)).where(Document.owner_id == user.id))
    ).scalar_one()
    return AdminUserOut(**AdminUserOut.model_validate(user).model_dump(exclude={"document_count"}), document_count=doc_count)


@router.get("/documents", response_model=list[DocumentListItem])
async def list_all_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.analyses).selectinload(Analysis.risk_findings))
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    items = []
    for doc in documents:
        latest = doc.latest_analysis
        high_risk_count = 0
        if latest:
            high_risk_count = sum(
                1
                for f in latest.risk_findings
                if f.severity in (RiskSeverity.HIGH, RiskSeverity.CRITICAL)
            )
        items.append(
            DocumentListItem(
                **DocumentOut.model_validate(doc).model_dump(),
                contract_type=latest.contract_type if latest else None,
                compliance_score=latest.compliance_score if latest else None,
                compliance_grade=latest.compliance_grade if latest else None,
                high_risk_count=high_risk_count,
            )
        )
    return items


@router.get("/logs", response_model=list[AuditLogOut])
async def list_audit_logs(
    level: str | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if level:
        stmt = stmt.where(AuditLog.level == level)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stats", response_model=SystemStatsOut)
async def get_system_stats(db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar_one()
    total_analyses = (await db.execute(select(func.count(Analysis.id)))).scalar_one()

    status_counts: dict[str, int] = {}
    for status in DocumentStatus:
        count = (
            await db.execute(select(func.count(Document.id)).where(Document.status == status))
        ).scalar_one()
        status_counts[status.value] = count

    avg_processing_seconds = None
    docs_with_times = await db.execute(
        select(Document.created_at, Document.processed_at).where(Document.processed_at.is_not(None))
    )
    durations = [
        (processed - created).total_seconds() for created, processed in docs_with_times.all()
    ]
    if durations:
        avg_processing_seconds = round(sum(durations) / len(durations), 2)

    return SystemStatsOut(
        total_users=total_users,
        total_documents=total_documents,
        total_analyses=total_analyses,
        total_groq_calls=groq_client_service.total_calls,
        average_processing_time_seconds=avg_processing_seconds,
        documents_by_status=status_counts,
    )

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.documents import _get_owned_document
from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.user import User
from app.schemas.analysis import AnalysisOut
from app.schemas.risk import RiskFindingOut

router = APIRouter(prefix="/api/documents", tags=["analysis"])


async def _get_latest_analysis(document_id: int, current_user: User, db: AsyncSession):
    document = await _get_owned_document(document_id, current_user, db)
    latest = document.latest_analysis
    if latest is None:
        raise NotFoundError("This document has not been analyzed yet")
    return latest


@router.get("/{document_id}/analysis", response_model=AnalysisOut)
async def get_analysis(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_latest_analysis(document_id, current_user, db)


@router.get("/{document_id}/risks", response_model=list[RiskFindingOut])
async def get_risks(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    analysis = await _get_latest_analysis(document_id, current_user, db)
    return analysis.risk_findings

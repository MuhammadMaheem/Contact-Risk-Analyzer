from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.analysis import _get_latest_analysis
from app.api.documents import _get_owned_document
from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportOut, ReportRequest
from app.services.audit_service import audit_service
from app.services.report_generator_service import report_generator_service

router = APIRouter(prefix="/api/documents", tags=["reports"])

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/{document_id}/report", response_model=ReportOut, status_code=201)
async def generate_report(
    document_id: int,
    payload: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await _get_owned_document(document_id, current_user, db)
    analysis = await _get_latest_analysis(document_id, current_user, db)
    findings = analysis.risk_findings

    if payload.format == "pdf":
        path = await report_generator_service.generate_pdf(document, analysis, findings)
    else:
        path = await report_generator_service.generate_docx(document, analysis, findings)

    report = Report(
        document_id=document.id,
        analysis_id=analysis.id,
        format=payload.format,
        file_path=str(path),
        generated_by_id=current_user.id,
    )
    db.add(report)
    await audit_service.log(
        db,
        action="report.generate",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        detail={"format": payload.format},
        commit=False,
    )
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await db.get(Report, report_id)
    if report is None:
        raise NotFoundError("Report not found")

    document = await _get_owned_document(report.document_id, current_user, db)
    file_path = Path(report.file_path)
    if not file_path.exists():
        raise NotFoundError("Report file is missing on disk")

    filename = f"{document.original_filename.rsplit('.', 1)[0]}_risk_report.{report.format.value}"
    return FileResponse(
        path=file_path,
        media_type=_MEDIA_TYPES[report.format.value],
        filename=filename,
    )

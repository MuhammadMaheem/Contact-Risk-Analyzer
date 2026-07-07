import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_client_ip, get_current_user
from app.exceptions import AuthorizationError, NotFoundError
from app.models.analysis import Analysis, RiskFinding
from app.models.document import Document
from app.models.enums import DocumentStatus, RiskSeverity, UserRole
from app.models.user import User
from app.schemas.document import DocumentListItem, DocumentOut, DocumentUploadResponse
from app.services.audit_service import audit_service
from app.services.document_processing_pipeline import document_processing_pipeline
from app.services.vector_store_service import vector_store_service
from app.utils.file_validation import validate_upload

router = APIRouter(prefix="/api/documents", tags=["documents"])
settings = get_settings()


async def _run_pipeline_in_background(document_id: int) -> None:
    await document_processing_pipeline.run(document_id)


@router.post("", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    file_type = validate_upload(file.filename or "upload", content)

    sha256_hash = hashlib.sha256(content).hexdigest()
    stored_filename = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload').name}"
    stored_path = settings.upload_dir / stored_filename
    stored_path.write_bytes(content)

    document = Document(
        owner_id=current_user.id,
        original_filename=file.filename or "upload",
        stored_path=str(stored_path),
        file_type=file_type,
        file_size_bytes=len(content),
        sha256_hash=sha256_hash,
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    await db.flush()
    await audit_service.log(
        db,
        action="document.upload",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        detail={"filename": document.original_filename, "size_bytes": document.file_size_bytes},
        ip_address=get_client_ip(request),
        commit=False,
    )
    await db.commit()
    await db.refresh(document)

    background_tasks.add_task(_run_pipeline_in_background, document.id)

    return DocumentUploadResponse(document=DocumentOut.model_validate(document))


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scope = [] if current_user.role == UserRole.ADMIN else [Document.owner_id == current_user.id]
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.analyses).selectinload(Analysis.risk_findings))
        .where(*scope)
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


async def _get_owned_document(document_id: int, current_user: User, db: AsyncSession) -> Document:
    document = await db.get(
        Document,
        document_id,
        options=[selectinload(Document.analyses).selectinload(Analysis.risk_findings)],
    )
    if document is None:
        raise NotFoundError("Document not found")
    if current_user.role != UserRole.ADMIN and document.owner_id != current_user.id:
        raise AuthorizationError("You do not have access to this document")
    return document


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await _get_owned_document(document_id, current_user, db)
    return document


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await _get_owned_document(document_id, current_user, db)
    vector_store_service.delete_document_chunks(document.id)
    stored_file = Path(document.stored_path)
    if stored_file.exists():
        stored_file.unlink()

    await audit_service.log(
        db,
        action="document.delete",
        user_id=current_user.id,
        resource_type="document",
        resource_id=document.id,
        ip_address=get_client_ip(request),
        commit=False,
    )
    await db.delete(document)
    await db.commit()


@router.post("/{document_id}/reprocess", response_model=DocumentOut, status_code=202)
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document = await _get_owned_document(document_id, current_user, db)
    document.status = DocumentStatus.UPLOADED
    document.status_detail = None
    await db.commit()
    background_tasks.add_task(_run_pipeline_in_background, document.id)
    return document

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.exceptions import AppException, DocumentParsingError
from app.models.analysis import Analysis, RiskFinding
from app.models.audit_log import AuditLog
from app.models.document import Document
from app.models.enums import AuditLevel, DocumentStatus
from app.schemas.analysis import ExtractionResult
from app.schemas.risk import RiskDetectionResult
from app.services.ai_extraction_service import AIExtractionService, ai_extraction_service
from app.services.compliance_score_service import ComplianceScoreService, compliance_score_service
from app.services.document_parser_service import DocumentParserService, document_parser_service
from app.services.embedding_service import EmbeddingService, embedding_service
from app.services.risk_detection_service import RiskDetectionService, risk_detection_service
from app.services.summarization_service import SummarizationService, summarization_service
from app.services.vector_store_service import VectorStoreService, vector_store_service
from app.utils.text_chunking import chunk_document_text

logger = logging.getLogger(__name__)


class DocumentProcessingPipeline:
    """Orchestrates the full AI workflow for one document: parse -> chunk/embed/index ->
    extract -> detect risk -> summarize -> score -> persist. Every stage catches its own
    exceptions and leaves the document in a terminal, queryable status — never stuck in
    `processing` forever."""

    def __init__(
        self,
        parser: DocumentParserService,
        embeddings: EmbeddingService,
        vector_store: VectorStoreService,
        extraction: AIExtractionService,
        risk_detection: RiskDetectionService,
        summarization: SummarizationService,
        compliance: ComplianceScoreService,
    ) -> None:
        self._parser = parser
        self._embeddings = embeddings
        self._vector_store = vector_store
        self._extraction = extraction
        self._risk_detection = risk_detection
        self._summarization = summarization
        self._compliance = compliance

    async def run(self, document_id: int) -> None:
        start = time.monotonic()
        async with AsyncSessionLocal() as db:
            document = await db.get(Document, document_id)
            if document is None:
                logger.error("Pipeline invoked for missing document_id=%s", document_id)
                return

            document.status = DocumentStatus.PROCESSING
            await db.commit()

            degraded = False
            extraction_result: ExtractionResult | None = None
            risk_result: RiskDetectionResult | None = None

            try:
                parsed = await self._parser.extract_text(document.stored_path, document.file_type)
            except DocumentParsingError as exc:
                document.status = DocumentStatus.FAILED
                document.status_detail = f"Parsing failed: {exc.message}"
                db.add(
                    AuditLog(
                        user_id=document.owner_id,
                        action="document.analyze.parse_failed",
                        resource_type="document",
                        resource_id=document.id,
                        level=AuditLevel.ERROR,
                        detail={"error": exc.message},
                    )
                )
                await db.commit()
                return

            document.page_count = parsed.page_count
            document.used_ocr = parsed.used_ocr
            document.extracted_text_char_count = len(parsed.text)
            text = parsed.text

            try:
                await self._index_chunks(document_id, text)
            except Exception as exc:  # noqa: BLE001
                degraded = True
                db.add(
                    AuditLog(
                        user_id=document.owner_id,
                        action="document.analyze.indexing_failed",
                        resource_type="document",
                        resource_id=document.id,
                        level=AuditLevel.WARNING,
                        detail={"error": str(exc)},
                    )
                )

            try:
                extraction_result = await self._extraction.extract(text)
            except AppException as exc:
                degraded = True
                db.add(
                    AuditLog(
                        user_id=document.owner_id,
                        action="document.analyze.extraction_failed",
                        resource_type="document",
                        resource_id=document.id,
                        level=AuditLevel.ERROR,
                        detail={"error": exc.message},
                    )
                )

            try:
                risk_result = await self._risk_detection.detect(text, extraction_result)
            except AppException as exc:
                degraded = True
                risk_result = RiskDetectionResult(findings=[])
                db.add(
                    AuditLog(
                        user_id=document.owner_id,
                        action="document.analyze.risk_detection_failed",
                        resource_type="document",
                        resource_id=document.id,
                        level=AuditLevel.ERROR,
                        detail={"error": exc.message},
                    )
                )

            summary_result = None
            try:
                summary_result = await self._summarization.summarize(extraction_result, risk_result)
            except AppException as exc:
                degraded = True
                db.add(
                    AuditLog(
                        user_id=document.owner_id,
                        action="document.analyze.summarization_failed",
                        resource_type="document",
                        resource_id=document.id,
                        level=AuditLevel.WARNING,
                        detail={"error": exc.message},
                    )
                )

            findings = risk_result.findings if risk_result else []
            score, grade = self._compliance.compute(findings)

            analysis = Analysis(
                document_id=document.id,
                contract_type=extraction_result.contract_type if extraction_result else None,
                parties=[p.model_dump() for p in extraction_result.parties] if extraction_result else [],
                effective_date=extraction_result.effective_date if extraction_result else None,
                expiry_date=extraction_result.expiry_date if extraction_result else None,
                payment_terms=extraction_result.payment_terms if extraction_result else None,
                renewal_clause=extraction_result.renewal_clause if extraction_result else None,
                confidentiality_clause=extraction_result.confidentiality_clause if extraction_result else None,
                termination_clause=extraction_result.termination_clause if extraction_result else None,
                responsibilities=(
                    [r.model_dump() for r in extraction_result.responsibilities] if extraction_result else []
                ),
                executive_summary=summary_result.executive_summary if summary_result else None,
                key_obligations=summary_result.key_obligations if summary_result else [],
                important_dates=(
                    [d.model_dump() for d in summary_result.important_dates] if summary_result else []
                ),
                important_clauses=summary_result.important_clauses if summary_result else [],
                recommended_actions=summary_result.recommended_actions if summary_result else [],
                compliance_score=score,
                compliance_grade=grade,
                raw_llm_extraction_json=extraction_result.model_dump_json() if extraction_result else None,
                model_used="llama-3.3-70b-versatile",
            )
            db.add(analysis)
            await db.flush()

            for f in findings:
                db.add(
                    RiskFinding(
                        analysis_id=analysis.id,
                        category=f.category,
                        severity=f.severity,
                        confidence=f.confidence,
                        title=f.title,
                        explanation=f.explanation,
                        supporting_clause_text=f.supporting_clause_text,
                        suggested_action=f.suggested_action,
                    )
                )

            document.status = DocumentStatus.PARTIAL if degraded else DocumentStatus.ANALYZED
            document.processed_at = datetime.now(timezone.utc)

            duration_ms = int((time.monotonic() - start) * 1000)
            db.add(
                AuditLog(
                    user_id=document.owner_id,
                    action="document.analyze.completed",
                    resource_type="document",
                    resource_id=document.id,
                    level=AuditLevel.INFO,
                    detail={"duration_ms": duration_ms, "degraded": degraded, "finding_count": len(findings)},
                )
            )
            await db.commit()

    async def _index_chunks(self, document_id: int, text: str) -> None:
        chunks = chunk_document_text(text)
        if not chunks:
            return
        embeddings = await self._embeddings.embed(chunks)
        self._vector_store.delete_document_chunks(document_id)
        self._vector_store.add_chunks(document_id, chunks, embeddings)


document_processing_pipeline = DocumentProcessingPipeline(
    parser=document_parser_service,
    embeddings=embedding_service,
    vector_store=vector_store_service,
    extraction=ai_extraction_service,
    risk_detection=risk_detection_service,
    summarization=summarization_service,
    compliance=compliance_score_service,
)


async def mark_stale_processing_documents_as_failed() -> None:
    """Crash-recovery sweep run at startup: any document stuck in `processing` from a
    previous (crashed) process run is marked failed and reprocessable, rather than
    silently stuck forever."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(Document.status == DocumentStatus.PROCESSING)
        )
        stale_docs = result.scalars().all()
        for doc in stale_docs:
            doc.status = DocumentStatus.FAILED
            doc.status_detail = "Processing was interrupted (server restarted). Please reprocess."
            db.add(
                AuditLog(
                    user_id=doc.owner_id,
                    action="document.analyze.stale_recovery",
                    resource_type="document",
                    resource_id=doc.id,
                    level=AuditLevel.WARNING,
                )
            )
        if stale_docs:
            await db.commit()
            logger.warning("Marked %d stale processing document(s) as failed on startup", len(stale_docs))

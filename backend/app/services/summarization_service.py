from app.config import get_settings
from app.exceptions import GroqAPIError, SummarizationError
from app.schemas.analysis import ExtractionResult
from app.schemas.risk import RiskDetectionResult
from app.schemas.summary import SummaryResult
from app.services.groq_client_service import GroqClientService, groq_client_service
from app.utils.prompts import SUMMARY_SYSTEM_PROMPT_V1

settings = get_settings()


class SummarizationService:
    """Synthesizes the executive summary from already-structured extraction + risk
    JSON (not raw text) — deliberately cheap since it's a synthesis step, not extraction."""

    def __init__(self, groq_client: GroqClientService) -> None:
        self._groq = groq_client

    async def summarize(
        self, extraction: ExtractionResult | None, risks: RiskDetectionResult | None
    ) -> SummaryResult:
        user_content = (
            f"EXTRACTION:\n{extraction.model_dump_json() if extraction else 'null'}\n\n"
            f"RISK FINDINGS:\n{risks.model_dump_json() if risks else 'null'}"
        )
        try:
            return await self._groq.chat_json(
                system_prompt=SUMMARY_SYSTEM_PROMPT_V1,
                user_content=user_content,
                schema_model=SummaryResult,
                model=settings.groq_summary_model,
            )
        except GroqAPIError as exc:
            raise SummarizationError(f"Summary generation failed: {exc.message}") from exc


summarization_service = SummarizationService(groq_client=groq_client_service)

from app.config import get_settings
from app.exceptions import GroqAPIError, RiskDetectionError
from app.schemas.analysis import ExtractionResult
from app.schemas.risk import RiskDetectionResult
from app.services.groq_client_service import GroqClientService, groq_client_service
from app.utils.prompts import RISK_DETECTION_SYSTEM_PROMPT_V1

settings = get_settings()

# Long contracts: bound the raw text sent alongside structured context to keep the call
# fast/cheap while still covering the parts most likely to contain risk language.
MAX_TEXT_CHARS_FOR_RISK_CALL = 15_000


class RiskDetectionService:
    def __init__(self, groq_client: GroqClientService) -> None:
        self._groq = groq_client

    async def detect(self, text: str, extraction: ExtractionResult | None) -> RiskDetectionResult:
        bounded_text = text[:MAX_TEXT_CHARS_FOR_RISK_CALL]
        extraction_json = extraction.model_dump_json() if extraction else "null"
        user_content = (
            f"STRUCTURED EXTRACTION (already parsed from this contract):\n{extraction_json}\n\n"
            f"CONTRACT TEXT:\n{bounded_text}"
        )
        try:
            return await self._groq.chat_json(
                system_prompt=RISK_DETECTION_SYSTEM_PROMPT_V1,
                user_content=user_content,
                schema_model=RiskDetectionResult,
                model=settings.groq_risk_model,
            )
        except GroqAPIError as exc:
            raise RiskDetectionError(f"Risk detection failed: {exc.message}") from exc


risk_detection_service = RiskDetectionService(groq_client=groq_client_service)

from app.config import get_settings
from app.exceptions import ExtractionError, GroqAPIError
from app.schemas.analysis import ExtractionResult
from app.services.groq_client_service import GroqClientService, groq_client_service
from app.utils.prompts import EXTRACTION_MERGE_SYSTEM_PROMPT_V1, EXTRACTION_SYSTEM_PROMPT_V1
from app.utils.text_chunking import chunk_document_text

settings = get_settings()

# Docs longer than this get map-then-merge extraction instead of a single call, to stay
# comfortably inside context limits and keep latency predictable.
MAP_REDUCE_THRESHOLD_CHARS = 12_000
MAP_CHUNK_TARGET_CHARS = 6_000


class AIExtractionService:
    def __init__(self, groq_client: GroqClientService) -> None:
        self._groq = groq_client

    async def extract(self, text: str) -> ExtractionResult:
        try:
            if len(text) <= MAP_REDUCE_THRESHOLD_CHARS:
                return await self._extract_single(text)
            return await self._extract_map_reduce(text)
        except GroqAPIError as exc:
            raise ExtractionError(f"Contract metadata extraction failed: {exc.message}") from exc

    async def _extract_single(self, text: str) -> ExtractionResult:
        return await self._groq.chat_json(
            system_prompt=EXTRACTION_SYSTEM_PROMPT_V1,
            user_content=text,
            schema_model=ExtractionResult,
            model=settings.groq_extraction_model,
        )

    async def _extract_map_reduce(self, text: str) -> ExtractionResult:
        sections = chunk_document_text(text, target_chars=MAP_CHUNK_TARGET_CHARS, min_chars=500)
        partials = [await self._extract_single(section) for section in sections]

        merge_input = "\n\n---PARTIAL---\n\n".join(p.model_dump_json() for p in partials)
        return await self._groq.chat_json(
            system_prompt=EXTRACTION_MERGE_SYSTEM_PROMPT_V1,
            user_content=merge_input,
            schema_model=ExtractionResult,
            model=settings.groq_summary_model,  # cheap model, pure synthesis of already-structured data
        )


ai_extraction_service = AIExtractionService(groq_client=groq_client_service)

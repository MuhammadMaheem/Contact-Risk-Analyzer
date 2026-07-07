import json
import logging
from typing import TypeVar

from groq import APIError, APITimeoutError, AsyncGroq
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.exceptions import GroqAPIError
from app.utils.prompts import build_extraction_repair_prompt

logger = logging.getLogger(__name__)
settings = get_settings()

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class GroqClientService:
    """Single choke point for every Groq call in the pipeline.

    Handles: JSON-mode invocation, json.loads + Pydantic validation, and exactly one
    automatic repair retry before raising — because Groq's JSON mode guarantees
    syntactically valid JSON but NOT schema conformance.
    """

    def __init__(self) -> None:
        self._client = AsyncGroq(api_key=settings.groq_api_key) if settings.groq_api_key else None
        self.total_calls = 0

    async def chat_json(
        self,
        system_prompt: str,
        user_content: str,
        schema_model: type[SchemaT],
        model: str,
        temperature: float = 0.1,
    ) -> SchemaT:
        if self._client is None:
            raise GroqAPIError(
                "GROQ_API_KEY is not configured",
                detail="Set GROQ_API_KEY in backend/.env",
            )

        raw_output = await self._call(system_prompt, user_content, model, temperature)
        self.total_calls += 1

        try:
            return schema_model.model_validate_json(raw_output)
        except (ValidationError, json.JSONDecodeError) as first_error:
            logger.warning("Groq output failed schema validation, retrying once: %s", first_error)

        repair_prompt = build_extraction_repair_prompt(
            invalid_output=raw_output,
            schema_hint=json.dumps(schema_model.model_json_schema()),
        )
        repaired_output = await self._call(system_prompt, repair_prompt, model, temperature=0.0)
        self.total_calls += 1

        try:
            return schema_model.model_validate_json(repaired_output)
        except (ValidationError, json.JSONDecodeError) as second_error:
            raise GroqAPIError(
                "Groq returned output that could not be parsed as valid JSON after one repair retry",
                detail=str(second_error),
            ) from second_error

    async def _call(self, system_prompt: str, user_content: str, model: str, temperature: float) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
            )
        except (APIError, APITimeoutError) as exc:
            raise GroqAPIError("Groq API call failed", detail=str(exc)) from exc

        content = response.choices[0].message.content
        if not content:
            raise GroqAPIError("Groq returned an empty response")
        return content

    async def chat_text(self, system_prompt: str, user_content: str, model: str, temperature: float = 0.2) -> str:
        if self._client is None:
            raise GroqAPIError(
                "GROQ_API_KEY is not configured", detail="Set GROQ_API_KEY in backend/.env"
            )
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=temperature,
            )
        except (APIError, APITimeoutError) as exc:
            raise GroqAPIError("Groq API call failed", detail=str(exc)) from exc
        self.total_calls += 1
        content = response.choices[0].message.content
        if not content:
            raise GroqAPIError("Groq returned an empty response")
        return content


groq_client_service = GroqClientService()

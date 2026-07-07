import asyncio
import logging

from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Wraps a singleton sentence-transformers model. Loaded once (expensive) and
    reused for the lifetime of the process; sync/CPU-bound calls run in a thread so
    they never block the event loop."""

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading embedding model %s (first use, may take a moment)...", settings.embedding_model_name)
            self._model = SentenceTransformer(settings.embedding_model_name, device="cpu")
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        embeddings = await asyncio.to_thread(model.encode, texts, convert_to_numpy=True)
        return embeddings.tolist()

    async def embed_one(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]

    def warm_up(self) -> None:
        """Call at startup so the first real request doesn't pay the model-load cost."""
        self._get_model()


embedding_service = EmbeddingService()

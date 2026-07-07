from app.config import get_settings
from app.exceptions import GroqAPIError, VectorStoreError
from app.schemas.search import SearchResultItem
from app.services.embedding_service import EmbeddingService, embedding_service
from app.services.groq_client_service import GroqClientService, groq_client_service
from app.services.vector_store_service import VectorStoreService, vector_store_service
from app.utils.prompts import RAG_QA_SYSTEM_PROMPT_V1

settings = get_settings()


class SemanticSearchService:
    """Serves both raw semantic search (mode='retrieve') and grounded RAG Q&A
    (mode='answer') from a single retrieval path — one embedding call, one Chroma
    query, then an optional Groq generation step layered on top."""

    def __init__(
        self,
        embeddings: EmbeddingService,
        vector_store: VectorStoreService,
        groq_client: GroqClientService,
    ) -> None:
        self._embeddings = embeddings
        self._vector_store = vector_store
        self._groq = groq_client

    async def retrieve(self, document_id: int, query: str, top_k: int = 5) -> list[SearchResultItem]:
        query_embedding = await self._embeddings.embed_one(query)
        try:
            raw_results = self._vector_store.query(document_id, query_embedding, top_k=top_k)
        except VectorStoreError:
            return []
        return [
            SearchResultItem(chunk_id=chunk_id, text=text, similarity=similarity)
            for chunk_id, text, similarity in raw_results
        ]

    async def answer(self, document_id: int, query: str, top_k: int = 5) -> tuple[str, list[SearchResultItem]]:
        sources = await self.retrieve(document_id, query, top_k=top_k)
        if not sources:
            return (
                "No indexed content is available for this document yet, so I can't answer "
                "grounded questions about it.",
                [],
            )

        excerpts = "\n\n".join(f"[Excerpt {i + 1}] {s.text}" for i, s in enumerate(sources))
        user_content = f"QUESTION: {query}\n\nEXCERPTS:\n{excerpts}"
        try:
            answer_text = await self._groq.chat_text(
                system_prompt=RAG_QA_SYSTEM_PROMPT_V1,
                user_content=user_content,
                model=settings.groq_rag_model,
            )
        except GroqAPIError as exc:
            answer_text = f"Could not generate an AI answer right now ({exc.message}). See retrieved excerpts below."
        return answer_text, sources


semantic_search_service = SemanticSearchService(
    embeddings=embedding_service,
    vector_store=vector_store_service,
    groq_client=groq_client_service,
)

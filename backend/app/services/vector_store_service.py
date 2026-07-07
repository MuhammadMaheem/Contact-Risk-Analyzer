import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.exceptions import VectorStoreError

logger = logging.getLogger(__name__)
settings = get_settings()

COLLECTION_NAME = "contract_chunks"


class VectorStoreService:
    """Wraps a single persistent ChromaDB collection shared across all documents,
    scoped per-query via a `document_id` metadata filter. Simpler lifecycle than
    one collection per document, and avoids Chroma collection-count bloat."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(COLLECTION_NAME)

    def add_chunks(self, document_id: int, chunks: list[str], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        try:
            ids = [f"doc{document_id}_chunk{i}" for i in range(len(chunks))]
            metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]
            self._collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Failed to index document chunks: {exc}") from exc

    def delete_document_chunks(self, document_id: int) -> None:
        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to delete chunks for document %s: %s", document_id, exc)

    def query(
        self, document_id: int, query_embedding: list[float], top_k: int = 5
    ) -> list[tuple[str, str, float]]:
        """Returns list of (chunk_id, text, similarity) sorted by similarity desc."""
        try:
            result = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"document_id": document_id},
            )
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError(f"Semantic search query failed: {exc}") from exc

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]

        # Chroma's default space is squared L2 on normalized embeddings; convert to a
        # 0-1 similarity-ish score for UI display (not a strict cosine similarity, but
        # monotonic and intuitive: smaller distance -> higher score).
        results = []
        for chunk_id, text, distance in zip(ids, documents, distances, strict=False):
            similarity = 1.0 / (1.0 + distance)
            results.append((chunk_id, text, round(similarity, 4)))
        return results


vector_store_service = VectorStoreService()

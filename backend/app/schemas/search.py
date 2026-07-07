from typing import Literal

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    mode: Literal["retrieve", "answer"] = "retrieve"
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResultItem(BaseModel):
    chunk_id: str
    text: str
    similarity: float


class RagAnswer(BaseModel):
    answer: str
    sources: list[SearchResultItem] = Field(default_factory=list)


class SearchResponse(BaseModel):
    mode: Literal["retrieve", "answer"]
    results: list[SearchResultItem] = Field(default_factory=list)
    answer: str | None = None

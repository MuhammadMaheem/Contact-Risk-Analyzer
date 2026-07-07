from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.documents import _get_owned_document
from app.database import get_db
from app.dependencies import get_current_user
from app.models.chat import SearchQueryLog
from app.models.user import User
from app.schemas.search import SearchQuery, SearchResponse
from app.services.semantic_search_service import semantic_search_service

router = APIRouter(prefix="/api/documents", tags=["search"])


@router.post("/{document_id}/search", response_model=SearchResponse)
async def search_document(
    document_id: int,
    payload: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_owned_document(document_id, current_user, db)

    if payload.mode == "answer":
        answer_text, sources = await semantic_search_service.answer(
            document_id, payload.query, top_k=payload.top_k
        )
        response = SearchResponse(mode="answer", results=sources, answer=answer_text)
    else:
        results = await semantic_search_service.retrieve(document_id, payload.query, top_k=payload.top_k)
        response = SearchResponse(mode="retrieve", results=results)

    db.add(
        SearchQueryLog(
            document_id=document_id,
            user_id=current_user.id,
            query_text=payload.query,
            mode=payload.mode,
            result_chunk_ids=[r.chunk_id for r in response.results],
            rag_answer=response.answer,
        )
    )
    await db.commit()

    return response

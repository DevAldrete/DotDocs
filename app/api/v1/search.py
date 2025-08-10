from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.core.search import semantic_search, keyword_search

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    k: int = 5
    semantic: bool = True


class SearchHit(BaseModel):
    id: str
    score: float
    text: str
    source_url: str | None = None
    explanation: str | None = None
    index: int | None = None


class SearchResponse(BaseModel):
    hits: List[SearchHit]


@router.post("", response_model=SearchResponse)
async def search_endpoint(payload: SearchRequest):
    if payload.semantic:
        pairs = await semantic_search(payload.query, k=payload.k)
    else:
        pairs = keyword_search(payload.query, k=payload.k)
    hits = [
        SearchHit(
            id=vec.id,
            score=score,
            text=vec.text,
            source_url=vec.meta.get("source_url"),
            explanation=vec.meta.get("explanation"),
            index=vec.meta.get("index"),
        )
        for vec, score in pairs
    ]
    return SearchResponse(hits=hits)

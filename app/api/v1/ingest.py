from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from app.core.ingest import ingest_url

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    url: HttpUrl
    reingest: bool = True


class IngestResponse(BaseModel):
    url: HttpUrl
    total_chunks: int
    stored: int


@router.post("", response_model=IngestResponse)
async def ingest_endpoint(payload: IngestRequest):
    try:
        res = await ingest_url(str(payload.url), reingest=payload.reingest)
        return IngestResponse(url=payload.url, total_chunks=res.total_chunks, stored=res.stored)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

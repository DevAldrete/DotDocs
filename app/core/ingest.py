"""High-level ingestion pipeline: fetch -> extract main content -> clean -> chunk -> embed -> store."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List
import uuid
import httpx
from bs4 import BeautifulSoup

from app.config.settings import get_settings
from .chunking import clean_text, chunk_text
from .embeddings import embed_texts
from .vectorstore import SqliteVectorStore, StoredVector
from .agents import generate_explanations


@dataclass
class IngestResult:
    url: str
    total_chunks: int
    stored: int


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(timeout=60, headers={"User-Agent": "DotDocsBot/0.1"}) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def extract_main_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove script/style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    # Prefer main / article / content
    candidates = []
    for selector in ["main", "article", "#content", "#main", ".content", "body"]:
        found = soup.select_one(selector)
        if found and len(found.get_text(strip=True)) > 200:
            candidates.append(found.get_text(" ", strip=True))
    if not candidates:
        return soup.get_text(" ")
    # Pick longest
    candidates.sort(key=len, reverse=True)
    return candidates[0]


async def ingest_url(url: str) -> IngestResult:
    settings = get_settings()
    vs = SqliteVectorStore(settings.vector_store_path)

    html = await fetch_html(url)
    raw_content = extract_main_content(html)
    cleaned = clean_text(raw_content)
    chunks = chunk_text(cleaned)

    embeddings = await embed_texts(chunks)
    explanations = await generate_explanations(chunks)

    vectors = [
        StoredVector(
            id=str(uuid.uuid4()),
            text=chunk,
            meta={"source_url": url, "index": i, "explanation": explanations[i]},
            embedding=emb,
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    vs.upsert(vectors)
    return IngestResult(url=url, total_chunks=len(chunks), stored=len(vectors))


async def ingest_urls(urls: List[str]) -> List[IngestResult]:
    return await asyncio.gather(*[ingest_url(u) for u in urls])

"""High-level ingestion pipeline: fetch -> extract main content -> clean -> chunk -> embed -> store."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List
import uuid
import httpx
from bs4 import BeautifulSoup
import structlog


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


async def fetch_html(url: str, retries: int = 3, backoff: float = 1.5) -> str:
    last_exc = None
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=60, headers={"User-Agent": "DotDocsBot/0.1"}) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text
        except Exception as e:  # pragma: no cover - network variability
            last_exc = e
            await asyncio.sleep(backoff * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_exc}")


def _density_score(node) -> float:
    text = node.get_text(" ", strip=True)
    if not text:
        return 0.0
    links = len(node.find_all("a")) + 1
    chars = len(text)
    return chars / links


def extract_main_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()
    candidates = []
    for tag in soup.find_all(["main", "article", "section", "div"]):
        score = _density_score(tag)
        text = tag.get_text(" ", strip=True)
        if len(text) < 200:
            continue
        candidates.append((score, len(text), text))
    if not candidates:
        body_text = soup.get_text(" ", strip=True)
        return body_text
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


logger = structlog.get_logger("ingest")


async def ingest_url(url: str, reingest: bool = True) -> IngestResult:
    settings = get_settings()
    vs = SqliteVectorStore(settings.vector_store_path)
    logger.info("fetch.start", url=url)
    html = await fetch_html(url)
    logger.info("fetch.done", url=url, size=len(html))
    raw_content = extract_main_content(html)
    logger.info("extract.done", url=url, length=len(raw_content))
    cleaned = clean_text(raw_content)
    chunks = chunk_text(cleaned)
    logger.info("chunk.done", url=url, chunks=len(chunks))

    embeddings = await embed_texts(chunks)
    logger.info("embed.done", url=url, embeddings=len(embeddings))
    explanations = await generate_explanations(chunks)
    logger.info("explain.done", url=url)

    # Deterministic IDs so we can re-ingest and overwrite without duplication
    vectors: List[StoredVector] = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        deterministic_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{url}::chunk::{i}"))
        vectors.append(
            StoredVector(
                id=deterministic_id,
                text=chunk,
                meta={"source_url": url, "index": i, "explanation": explanations[i]},
                embedding=emb,
            )
        )
    if reingest:
        # Delete any stale chunks with same source that are not in new set
        existing = vs.by_source(url)
        keep_ids = {v.id for v in vectors}
        to_delete = [v.id for v in existing if v.id not in keep_ids]
        vs.delete_ids(to_delete)
        logger.info("reingest.cleanup", url=url, deleted=len(to_delete))
    vs.upsert(vectors)
    logger.info("ingest.upsert", url=url, stored=len(vectors))
    return IngestResult(url=url, total_chunks=len(chunks), stored=len(vectors))


async def ingest_urls(urls: List[str]) -> List[IngestResult]:
    return await asyncio.gather(*[ingest_url(u) for u in urls])

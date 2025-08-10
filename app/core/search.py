"""Search interface for keyword + semantic retrieval."""
from __future__ import annotations

from typing import List, Tuple
import math
import re

from app.config.settings import get_settings
from .embeddings import embed_texts
from .vectorstore import SqliteVectorStore, StoredVector


async def semantic_search(query: str, k: int = 5) -> List[Tuple[StoredVector, float]]:
    settings = get_settings()
    vs = SqliteVectorStore(settings.vector_store_path)
    emb = (await embed_texts([query]))[0]
    return vs.similarity_search(emb, top_k=k)


def keyword_search(query: str, k: int = 5) -> List[Tuple[StoredVector, float]]:
    settings = get_settings()
    vs = SqliteVectorStore(settings.vector_store_path)
    terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    scored: List[Tuple[StoredVector, float]] = []
    all_ids = []
    # naive select all
    results = vs.similarity_search([0.0], top_k=vs.count())  # hack to get all
    for vec, _ in results:
        text_l = vec.text.lower()
        score = sum(text_l.count(t) for t in terms)
        if score > 0:
            scored.append((vec, float(score)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]

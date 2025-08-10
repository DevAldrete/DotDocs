"""Embedding provider abstraction using official client SDKs.

Supported providers (set via APP_EMBEDDING_PROVIDER):
 - openai   (default) -> OpenAI `AsyncOpenAI` client
 - pinecone -> Pinecone Inference API (`pc.inference.embed`)
 - qdrant   -> Local FastEmbed via `qdrant-client[fastembed]` (if installed)

Public helper: `embed_texts(List[str]) -> List[List[float]]` (async)
"""

from __future__ import annotations

from typing import List, Protocol, Optional
import asyncio

from app.config.settings import get_settings

# --- OpenAI -----------------------------------------------------------------
try:  # openai>=1.x new client
    from openai import AsyncOpenAI  # type: ignore
except ImportError:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore

# --- Pinecone ---------------------------------------------------------------
try:
    from pinecone import Pinecone  # type: ignore
except ImportError:  # pragma: no cover
    Pinecone = None  # type: ignore

# --- Qdrant / FastEmbed -----------------------------------------------------
try:
    from fastembed import TextEmbedding  # provided by qdrant-client[fastembed]
except Exception:  # pragma: no cover - optional dependency
    TextEmbedding = None  # type: ignore


class Embedder(Protocol):  # pragma: no cover - structural typing only
    async def embed(self, texts: List[str]) -> List[List[float]]: ...


# ---------------------- Provider Implementations ---------------------------
class OpenAIEmbedder:
    def __init__(self, api_key: str, model: str):
        if not AsyncOpenAI:
            raise RuntimeError("openai package >=1.0 not available")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        # OpenAI API handles batching; we send all at once for now.
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        # resp.data is a list with .embedding
        return [d.embedding for d in resp.data]


class PineconeEmbedder:
    """Use Pinecone's inference.embed endpoint to produce embeddings.

    NOTE: Requires a Pinecone API key.
    """

    def __init__(self, api_key: str, model: str):
        if not Pinecone:
            raise RuntimeError("pinecone package not installed")
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY missing")
        self.pc = Pinecone(api_key=api_key)
        self.model = model

    async def embed(self, texts: List[str]) -> List[List[float]]:
        def _call():
            return self.pc.inference.embed(
                model=self.model,
                inputs=texts,
                parameters={"input_type": "passage", "truncate": "END"},
            )

        resp = await asyncio.to_thread(_call)

        # Attempt to normalize output into List[List[float]]
        # Depending on SDK version response may already be list of vectors
        if isinstance(resp, list):
            return resp  # assume already List[List[float]]
        if isinstance(resp, dict) and "data" in resp:
            out: List[List[float]] = []
            for item in resp["data"]:
                if isinstance(item, dict):
                    if "values" in item:
                        out.append(item["values"])  # new field name
                    elif "embedding" in item:
                        out.append(item["embedding"])
            if out:
                return out
        raise RuntimeError("Unexpected Pinecone embed response format")


class QdrantEmbedder:
    """Embed via local FastEmbed models (qdrant-client[fastembed]).

    This keeps Qdrant focused on storage; we only use its recommended fastembed
    integration for generation. Configure APP_OPENAI_EMBEDDING_MODEL with a
    compatible FastEmbed model name when provider=qdrant.
    """

    def __init__(self, model: str):
        if TextEmbedding is None:
            raise RuntimeError(
                "fastembed not available. Install 'qdrant-client[fastembed]' to use provider=qdrant."
            )
        self._embedder = TextEmbedding(model_name=model)

    async def embed(self, texts: List[str]) -> List[List[float]]:
        def _run():
            # fastembed generator -> list
            return list(self._embedder.embed(texts))

        return await asyncio.to_thread(_run)


# ---------------------------- Factory / Cache ------------------------------
_EMBEDDER: Optional[Embedder] = None


def _build_embedder() -> Embedder:
    settings = get_settings()
    provider = settings.embedding_provider.lower()
    if provider == "openai":
        return OpenAIEmbedder(settings.openai_api_key, settings.openai_embedding_model)
    if provider == "pinecone":
        return PineconeEmbedder(settings.pinecone_api_key, settings.openai_embedding_model)
    if provider == "qdrant":
        # Using openai_embedding_model setting as generic model name
        return QdrantEmbedder(settings.openai_embedding_model)
    raise ValueError(f"Unknown embedding provider: {provider}")


async def _get_embedder() -> Embedder:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = _build_embedder()
    return _EMBEDDER


async def embed_texts(texts: List[str]) -> List[List[float]]:
    embedder = await _get_embedder()
    return await embedder.embed(texts)


__all__ = ["embed_texts", "OpenAIEmbedder", "PineconeEmbedder", "QdrantEmbedder"]

"""OpenAI embedding helper (can be swapped later)."""
from __future__ import annotations

from typing import List
import os
import httpx

from app.config.settings import get_settings


async def embed_texts(texts: List[str]) -> List[List[float]]:
    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY missing")
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {api_key}"}
    model = settings.openai_embedding_model
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json={"model": model, "input": texts}, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return [d["embedding"] for d in data["data"]]

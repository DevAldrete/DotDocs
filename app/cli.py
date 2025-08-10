"""Typer CLI for ingestion and search."""
from __future__ import annotations

import asyncio
import typer
from typing import Optional

from app.core.ingest import ingest_url
from app.core.search import semantic_search, keyword_search

app = typer.Typer(add_completion=False, help="DotDocs CLI")


@app.command()
def ingest(url: str):
    """Ingest a single URL into the local vector store."""
    res = asyncio.run(ingest_url(url))
    typer.echo(f"Ingested {url} -> {res.stored} chunks")


@app.command()
def search(query: str, k: int = typer.Option(5, help="Top K"), semantic: bool = typer.Option(True, help="Use semantic search")):
    """Search stored snippets."""
    if semantic:
        results = asyncio.run(semantic_search(query, k=k))
    else:
        results = keyword_search(query, k=k)
    for vec, score in results:
        typer.echo("-" * 60)
        typer.echo(f"Score: {score:.4f} | Source: {vec.meta.get('source_url')} (#{vec.meta.get('index')})")
        expl = vec.meta.get("explanation")
        if expl:
            typer.echo(f"Explanation: {expl}")
        typer.echo(vec.text[:500])
    typer.echo("-" * 60)


if __name__ == "__main__":  # pragma: no cover
    app()

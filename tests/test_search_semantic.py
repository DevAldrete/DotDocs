import asyncio
from app.core.ingest import ingest_url
from app.core.search import semantic_search


async def _prep():
    # Ingest example.com (minimal text); semantic search may return something
    await ingest_url("https://example.com", reingest=True)


def test_semantic_search_runs():
    asyncio.run(_prep())
    # Query generic term; ensure no crash; may return 0-5 results
    res = asyncio.run(semantic_search("example domain", k=3))
    assert isinstance(res, list)

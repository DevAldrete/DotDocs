import asyncio
from app.core.ingest import ingest_url
from app.config.settings import get_settings
from app.core.vectorstore import SqliteVectorStore


async def _run():
    # Use a tiny data URL to avoid network variability; simple HTML inline.
    html_url = "https://example.com"  # stable small page
    await ingest_url(html_url, reingest=True)
    settings = get_settings()
    vs = SqliteVectorStore(settings.vector_store_path)
    first = vs.by_source(html_url)
    ids_first = {v.id for v in first}
    # Re-ingest and confirm ids stable
    await ingest_url(html_url, reingest=True)
    second = vs.by_source(html_url)
    ids_second = {v.id for v in second}
    print("First IDs:", ids_first)
    print("Second IDs:", ids_second)
    assert ids_first == ids_second


def test_deterministic_ids():
    asyncio.run(_run())

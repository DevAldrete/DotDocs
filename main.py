from fastapi import FastAPI
import structlog
from app.cli import app as cli_app
from app.api.v1.ingest import router as ingest_router
from app.api.v1.search import router as search_router


logger = structlog.get_logger("dotdocs")


def build_app() -> FastAPI:
    api = FastAPI(
        title="DotDocs API",
        version="0.1.0",
        openapi_tags=[
            {"name": "ingest", "description": "Endpoints to ingest documentation sources."},
            {"name": "search", "description": "Query stored atomic snippets via semantic or keyword."},
            {"name": "meta", "description": "Operational / health endpoints."},
        ],
    )
    api.include_router(ingest_router)
    api.include_router(search_router)
    @api.get("/health", tags=["meta"])
    async def health():  # pragma: no cover - simple
        return {"status": "ok"}
    return api


app = build_app()


def main():  # pragma: no cover - CLI entry
    cli_app()


if __name__ == "__main__":  # pragma: no cover
    main()

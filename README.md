# DotDocs

DotDocs is a lightweight tool for extracting **clear, self-contained, and well-explained** information or code snippets from any documentation, tutorial, or manual.  
You give it a link, it gives you exactly what you need — no scrolling through 20 pages of “Hello World” fluff.

---

## Features

- **URL ingestion** – Add any HTML, Markdown, or PDF doc/tutorial/manual link.
- **Atomic snippet extraction** – Breaks content into small, self-contained knowledge units.
- **Context-aware search** – Find snippets with plain keywords or natural language.
- **Human-readable explanations** – Each snippet comes with a short, clear explanation.
- **Original source reference** – Always links back to the original document section.

---

## Use Cases

- Quickly retrieve code examples without digging through entire docs.
- Store personal “knowledge cards” for repeated queries.
- Learn from tutorials in small, digestible pieces.

---

## Tech Stack

- **Backend**: Python (FastAPI)
- **Parsing**: BeautifulSoup or Scrapy / Readability for HTML, pdfplumber for PDFs, Markdown parsers
- **Search**: Local vector database (Chroma) or hosted (Pinecone, Weaviate)
- **Frontend**: React + TailwindCSS
- **AI Layer**: OpenAI embeddings + LLM explanations

---

## Installation

_(Coming soon — once MVP is ready)_

## Usage (MVP)

### Run the API

```bash
uvicorn main:app --reload
```

Then:

POST /ingest with JSON `{ "url": "https://example.com" }` to ingest a page.

POST /search with `{ "query": "authentication middleware", "k": 5, "semantic": true }` to retrieve snippets.

GET /health returns `{ "status": "ok" }`.

Interactive docs at `/docs` (Swagger) and `/redoc` if enabled.

### CLI

```bash
python -m app.cli ingest https://example.com/docs
python -m app.cli search "dependency injection" --k 5
```

### Crawler (multi-page)

Programmatic crawl & ingest of a docs site (same-domain links):

```python
import asyncio
from app.core.scraper import crawl_and_ingest

async def run():
	pages = await crawl_and_ingest("https://example.com/docs", max_pages=25)
	print("Crawled", len(pages), "pages")

asyncio.run(run())
```

### Environment Variables

Key vars (prefix with APP_ if using settings overrides):
- OPENAI_API_KEY (for embeddings & explanations when provider = openai)
- QDRANT_API_KEY (if using embedding_provider=qdrant)
- PINECONE_API_KEY / PINECONE_ENVIRONMENT (if using embedding_provider=pinecone)

### Switching Embedding Provider

Set `APP_EMBEDDING_PROVIDER` to one of: `openai` (default), `qdrant`, `pinecone`.

### Deterministic Re-ingestion

Re-ingesting a URL replaces stale chunks without duplication (UUIDv5 ids based on url+index).

---

## Roadmap

- [ ] MVP: Single URL ingestion + snippet retrieval
- [ ] Multiple URL ingestion & indexing
- [ ] Offline cache
- [ ] Browser extension
- [ ] CLI interface
- [ ] Multi-format export (Markdown, JSON, PDF)

---

## License

Apache License 2.0

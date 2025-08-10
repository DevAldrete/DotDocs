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

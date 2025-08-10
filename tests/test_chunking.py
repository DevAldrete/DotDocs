from app.core.chunking import chunk_text


def test_chunk_basic():
    text = "FastAPI is a modern, fast web framework for building APIs with Python. " * 5
    chunks = chunk_text(text)
    assert len(chunks) >= 1
    assert all(len(c) > 0 for c in chunks)

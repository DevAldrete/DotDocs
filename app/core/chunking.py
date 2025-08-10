"""Content chunking utilities using spaCy for sentence + token aware splitting."""
from __future__ import annotations

from typing import List, Iterable
import re
import spacy
from app.config.settings import get_settings

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback simple sentencizer if model not installed yet
            nlp = spacy.blank("en")
            sbd = nlp.add_pipe("sentencizer")
            _nlp = nlp
    return _nlp


def clean_text(text: str) -> str:
    # Basic cleanliness: collapse whitespace, strip
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str) -> List[str]:
    settings = get_settings()
    max_chars = settings.max_snippet_chars
    target_tokens = settings.target_snippet_tokens

    nlp = _get_nlp()
    doc = nlp(text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        if not sent:
            continue
        if current_len + len(sent) > max_chars or len(current) > 12:  # safety
            if current:
                chunks.append(" ".join(current).strip())
            current = [sent]
            current_len = len(sent)
        else:
            current.append(sent)
            current_len += len(sent)
    if current:
        chunks.append(" ".join(current).strip())

    # If any single sentence too long just hard cut
    normalized: List[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            normalized.append(c)
        else:
            # naive split
            for i in range(0, len(c), max_chars):
                normalized.append(c[i : i + max_chars])
    return normalized

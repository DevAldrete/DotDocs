"""Simple local vector store wrapper (Chroma-like interface abstraction).
Currently a lightweight in-process store using sqlite + cosine similarity.
We abstract so we can later swap to real Chroma / Pinecone without touching callers.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
import math
import sqlite3
import json



@dataclass
class StoredVector:
    id: str
    text: str
    meta: dict
    embedding: List[float]


class SqliteVectorStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vectors(
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                metadata TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
            """
        )
        self.conn.commit()

    def upsert(self, items: Sequence[StoredVector]):
        cur = self.conn.cursor()
        cur.executemany(
            "INSERT OR REPLACE INTO vectors(id, text, metadata, embedding) VALUES(?,?,?,?)",
            [
                (
                    v.id,
                    v.text,
                    json.dumps(v.meta, ensure_ascii=False),
                    json.dumps(v.embedding),
                )
                for v in items
            ],
        )
        self.conn.commit()

    def all(self) -> List[StoredVector]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, text, metadata, embedding FROM vectors")
        rows = cur.fetchall()
        return [StoredVector(id=r[0], text=r[1], meta=json.loads(r[2]), embedding=json.loads(r[3])) for r in rows]

    def by_source(self, source_url: str) -> List[StoredVector]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, text, metadata, embedding FROM vectors WHERE json_extract(metadata, '$.source_url') = ?", (source_url,))
        rows = cur.fetchall()
        return [StoredVector(id=r[0], text=r[1], meta=json.loads(r[2]), embedding=json.loads(r[3])) for r in rows]

    def delete_ids(self, ids: Sequence[str]):
        if not ids:
            return
        cur = self.conn.cursor()
        qmarks = ",".join(["?"] * len(ids))
        cur.execute(f"DELETE FROM vectors WHERE id IN ({qmarks})", list(ids))
        self.conn.commit()

    def fetch(self, ids: Sequence[str]) -> List[StoredVector]:
        qmarks = ",".join(["?"] * len(ids))
        cur = self.conn.cursor()
        cur.execute(f"SELECT id, text, metadata, embedding FROM vectors WHERE id IN ({qmarks})", list(ids))
        rows = cur.fetchall()
        return [StoredVector(id=r[0], text=r[1], meta=json.loads(r[2]), embedding=json.loads(r[3])) for r in rows]

    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[Tuple[StoredVector, float]]:
        cur = self.conn.cursor()
        cur.execute("SELECT id, text, metadata, embedding FROM vectors")
        rows = cur.fetchall()
        scored: List[Tuple[StoredVector, float]] = []
        for r in rows:
            emb = json.loads(r[3])
            sim = _cosine(query_embedding, emb)
            scored.append(
                (
                    StoredVector(id=r[0], text=r[1], meta=json.loads(r[2]), embedding=emb),
                    sim,
                )
            )
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vectors")
        return int(cur.fetchone()[0])


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


__all__ = ["SqliteVectorStore", "StoredVector"]

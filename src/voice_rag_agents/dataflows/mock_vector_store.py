"""Deterministic in-memory mock vector store.

Supports upsert, search (nearest-first by cosine similarity), metadata
filtering, and delete-by-document-id.  Satisfies the ``VectorStore``
interface defined in :mod:`voice_rag_agents.dataflows.interfaces`.
"""

from __future__ import annotations

import math

from voice_rag_agents.dataflows.vector_records import (
    SearchRequest,
    SearchResult,
    VectorRecord,
)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors (both assumed non-zero)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for b_ in [b] for x in b_)) or 1.0
    return dot / (norm_a * norm_b)


def _matches_filters(metadata: dict, filters: dict | None) -> bool:
    """Return True when *metadata* satisfies all key/value pairs in *filters*."""
    if not filters:
        return True
    return all(metadata.get(k) == v for k, v in filters.items())


class MockVectorStore:
    """In-memory vector store with cosine-similarity search.

    Fully deterministic and requires no external services.  Suitable for
    unit tests, graph-path tests, and contract tests.
    """

    def __init__(self) -> None:
        self._collections: dict[str, dict[str, VectorRecord]] = {}

    # -- VectorStore interface -----------------------------------------------

    def health(self) -> dict:
        return {"status": "ok", "provider": "mock"}

    def ensure_collection(self, name: str, dimension: int) -> None:
        if name not in self._collections:
            self._collections[name] = {}

    def upsert(
        self, collection: str, records: list[VectorRecord]
    ) -> dict:
        self.ensure_collection(collection, 0)
        col = self._collections[collection]
        for rec in records:
            col[rec.id] = rec
        return {"upserted": len(records)}

    def search(
        self, collection: str, request: SearchRequest
    ) -> list[SearchResult]:
        col = self._collections.get(collection, {})
        query_vec = request.query_vector
        hits: list[SearchResult] = []

        for rec in col.values():
            if not _matches_filters(rec.metadata, request.filters):
                continue
            score = _cosine_similarity(query_vec, rec.vector)
            hits.append(
                SearchResult(
                    id=rec.id,
                    chunk_id=rec.chunk_id,
                    chunk_text=rec.chunk_text,
                    score=score,
                    metadata=rec.metadata,
                    document_id=rec.document_id,
                )
            )

        # Nearest-first (highest cosine similarity first)
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[: request.top_k]

    def delete_by_document_id(
        self, collection: str, document_id: str
    ) -> dict:
        col = self._collections.get(collection, {})
        to_delete = [
            k for k, v in col.items() if v.document_id == document_id
        ]
        for k in to_delete:
            del col[k]
        return {"deleted": len(to_delete)}

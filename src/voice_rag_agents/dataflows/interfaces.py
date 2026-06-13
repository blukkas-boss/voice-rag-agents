"""Provider interfaces for dataflows (vector store).

See ``docs/blueprint/09_MODULE_CONTRACTS_AND_INTERFACES.md`` for the
authoritative contract specification.
"""

from __future__ import annotations

from typing import Protocol

from voice_rag_agents.dataflows.vector_records import (
    SearchRequest,
    SearchResult,
    VectorRecord,
)


class VectorStore(Protocol):
    """Vector store provider interface.

    Supports collection lifecycle (create, delete) and basic CRUD + search
    with metadata filtering.  Every adapter — Milvus, in-memory mock,
    future Pinecone/Weaviate/... — must satisfy this protocol.
    """

    def health(self) -> dict:
        """Return a health-check dict."""
        ...

    def ensure_collection(self, name: str, dimension: int) -> None:
        """Create the collection if it does not exist."""
        ...

    def upsert(self, collection: str, records: list[VectorRecord]) -> dict:
        """Upsert vector records into a collection."""
        ...

    def search(
        self, collection: str, request: SearchRequest
    ) -> list[SearchResult]:
        """Search for similar vectors."""
        ...

    def delete_by_document_id(
        self, collection: str, document_id: str
    ) -> dict:
        """Delete all records belonging to a document."""
        ...

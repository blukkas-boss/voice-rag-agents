"""Vector record and search-request schemas for the vector-store layer.

These models are shared between ``VectorStore`` interfaces, Milvus adapter,
and mock implementations.  Field shapes follow the contracts in
``docs/blueprint/09_MODULE_CONTRACTS_AND_INTERFACES.md``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VectorRecord(BaseModel):
    """A single vector-store record (chunk text + embedding + metadata)."""

    id: str
    document_id: str
    chunk_id: str
    chunk_text: str = ""
    vector: list[float] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SearchRequest(BaseModel):
    """Parameters for a vector-store similarity search."""

    query_vector: list[float]
    top_k: int = 5
    filters: dict | None = None
    output_fields: list[str] = Field(
        default_factory=lambda: ["chunk_text", "metadata"]
    )


class SearchResult(BaseModel):
    """Single vector-store search hit."""

    id: str
    chunk_id: str
    chunk_text: str
    score: float
    metadata: dict
    document_id: str = ""
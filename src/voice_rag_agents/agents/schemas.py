"""Domain schemas — typed, serializable records for the voice RAG product.

All public records are Pydantic v2 models so they serialize to/from dict/JSON
with zero extra code.  Field shapes follow the contracts defined in
``docs/blueprint/09_MODULE_CONTRACTS_AND_INTERFACES.md``.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from voice_rag_agents.dataflows.vector_records import SearchResult, VectorRecord


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------


class DocumentRecord(BaseModel):
    """A parsed, normalized source document."""

    document_id: str
    source_file: str
    source_type: str = "markdown"
    title: str = ""
    text: str = ""
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Chunk
# ---------------------------------------------------------------------------


class ChunkRecord(BaseModel):
    """A single chunk of a document after splitting."""

    chunk_id: str
    document_id: str
    sequence: int
    section: str = ""
    text: str = ""
    token_count: int = 0
    metadata: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


class EmbeddingResult(BaseModel):
    """Output of an embedding call for one or more texts."""

    vectors: list[list[float]]
    model: str = ""
    dimension: int = 0
    token_usage: dict | None = None
    provider_metadata: dict = Field(default_factory=dict)


class EmbeddingRecord(BaseModel):
    """Chunk + its vector embedding, ready for vector-store upsert."""

    chunk_id: str
    document_id: str
    vector: list[float] = Field(default_factory=list)
    model: str = ""
    dimension: int = 0


# ---------------------------------------------------------------------------
# Search / retrieval
# ---------------------------------------------------------------------------


# SearchResult and SearchRequest are defined in dataflows.vector_records.
# Re-exported here for convenience.


class Citation(BaseModel):
    """A source citation attached to a generated answer."""

    label: str  # e.g. "S1"
    chunk_id: str
    source_file: str
    section: str = ""
    text: str = ""


# ---------------------------------------------------------------------------
# Graph error
# ---------------------------------------------------------------------------


class GraphError(BaseModel):
    """Structured error propagated through the graph state."""

    code: str
    message: str
    node: str = ""
    retryable: bool = False
    details: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Config schema (re-export for consumers that only import schemas)
# ---------------------------------------------------------------------------

# Re-exports for convenience
__all__ = [
    "ChunkRecord",
    "Citation",
    "DocumentRecord",
    "EmbeddingRecord",
    "EmbeddingResult",
    "GraphError",
    "SearchResult",
    "VectorRecord",
]

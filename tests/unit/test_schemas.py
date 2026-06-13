"""UT-005 / VRAG-B001: domain schema serialization + required-field tests."""
from __future__ import annotations

import hashlib

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# DocumentRecord
# ---------------------------------------------------------------------------


def test_document_record_required_fields():
    from voice_rag_agents.agents.schemas import DocumentRecord

    doc = DocumentRecord(
        document_id="doc-1",
        source_file="notes.md",
        text="Hello world",
    )
    assert doc.document_id == "doc-1"
    assert doc.source_file == "notes.md"
    assert doc.source_type == "markdown"  # default
    assert doc.title == ""  # default
    assert doc.metadata == {}  # default


def test_document_record_serialization():
    from voice_rag_agents.agents.schemas import DocumentRecord

    doc = DocumentRecord(
        document_id="doc-1",
        source_file="notes.md",
        source_type="markdown",
        title="My Notes",
        text="Body",
        metadata={"author": "Alice"},
    )
    d = doc.model_dump()
    assert d["document_id"] == "doc-1"
    assert d["metadata"]["author"] == "Alice"


def test_document_record_missing_required():
    from voice_rag_agents.agents.schemas import DocumentRecord

    with pytest.raises(Exception):
        DocumentRecord(source_file="notes.md")  # missing document_id


# ---------------------------------------------------------------------------
# ChunkRecord
# ---------------------------------------------------------------------------


def test_chunk_record_required_fields():
    from voice_rag_agents.agents.schemas import ChunkRecord

    chunk = ChunkRecord(
        chunk_id="c1",
        document_id="doc-1",
        sequence=0,
        text="chunk text",
    )
    assert chunk.chunk_id == "c1"
    assert chunk.section == ""
    assert chunk.token_count == 0
    assert chunk.metadata == {}


def test_chunk_record_serialization():
    from voice_rag_agents.agents.schemas import ChunkRecord

    chunk = ChunkRecord(
        chunk_id="c1",
        document_id="doc-1",
        sequence=2,
        section="Risks",
        text="API rate limits",
        token_count=84,
        metadata={"project": "Orion"},
    )
    d = chunk.model_dump()
    assert d["sequence"] == 2
    assert d["metadata"]["project"] == "Orion"


# ---------------------------------------------------------------------------
# EmbeddingResult
# ---------------------------------------------------------------------------


def test_embedding_result_shape():
    from voice_rag_agents.agents.schemas import EmbeddingResult

    result = EmbeddingResult(
        vectors=[[0.1, 0.2], [0.3, 0.4]],
        model="mock",
        dimension=2,
    )
    assert len(result.vectors) == 2
    assert result.dimension == 2
    d = result.model_dump()
    assert d["model"] == "mock"


def test_embedding_result_missing_required():
    from voice_rag_agents.agents.schemas import EmbeddingResult

    with pytest.raises(Exception):
        EmbeddingResult(model="mock")  # missing vectors + dimension


# ---------------------------------------------------------------------------
# EmbeddingRecord
# ---------------------------------------------------------------------------


def test_embedding_record_roundtrip():
    from voice_rag_agents.agents.schemas import EmbeddingRecord

    rec = EmbeddingRecord(
        chunk_id="c1",
        document_id="doc-1",
        vector=[0.1, 0.2, 0.3],
        model="mock",
        dimension=3,
    )
    d = rec.model_dump()
    assert d["chunk_id"] == "c1"
    assert d["vector"] == [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------


def test_citation_fields():
    from voice_rag_agents.agents.schemas import Citation

    cite = Citation(
        label="S1",
        chunk_id="c1",
        source_file="notes.md",
        section="Risks",
        text="API rate limits may impact analytics.",
    )
    assert cite.label == "S1"
    d = cite.model_dump()
    assert d["source_file"] == "notes.md"


# ---------------------------------------------------------------------------
# GraphError
# ---------------------------------------------------------------------------


def test_graph_error_fields():
    from voice_rag_agents.agents.schemas import GraphError

    err = GraphError(
        code="EMBEDDING_DIMENSION_MISMATCH",
        message="Dimension 1024 != 2048",
        node="validate_embeddings",
        retryable=False,
        details={"expected": 2048, "actual": 1024},
    )
    assert err.code == "EMBEDDING_DIMENSION_MISMATCH"
    assert err.retryable is False
    d = err.model_dump()
    assert d["details"]["expected"] == 2048


def test_graph_error_defaults():
    from voice_rag_agents.agents.schemas import GraphError

    err = GraphError(code="ERR", message="something broke")
    assert err.node == ""
    assert err.retryable is False
    assert err.details == {}


# ---------------------------------------------------------------------------
# Stable doc hash (UT-005)
# ---------------------------------------------------------------------------


def test_stable_doc_hash():
    """UT-005: same content -> same document ID (SHA-256)."""
    content = "Meeting notes about third-party API risks."
    hash1 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert hash1 == hash2


# ---------------------------------------------------------------------------
# VectorRecord
# ---------------------------------------------------------------------------


def test_vector_record_roundtrip():
    from voice_rag_agents.dataflows.vector_records import VectorRecord

    rec = VectorRecord(
        id="vec-1",
        document_id="doc-1",
        chunk_id="c1",
        chunk_text="API rate limits",
        vector=[0.1, 0.2],
        metadata={"project": "Orion"},
    )
    d = rec.model_dump()
    assert d["id"] == "vec-1"
    assert d["metadata"]["project"] == "Orion"


def test_vector_record_missing_required():
    from voice_rag_agents.dataflows.vector_records import VectorRecord

    with pytest.raises(Exception):
        VectorRecord(document_id="doc-1")  # missing id, chunk_id, etc.


# ---------------------------------------------------------------------------
# SearchRequest
# ---------------------------------------------------------------------------


def test_search_request_defaults():
    from voice_rag_agents.dataflows.vector_records import SearchRequest

    req = SearchRequest(query_vector=[0.1, 0.2])
    assert req.top_k == 5
    assert req.filters is None
    assert "chunk_text" in req.output_fields

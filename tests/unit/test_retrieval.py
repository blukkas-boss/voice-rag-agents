"""Unit tests for retrieval module — no external services required."""

from __future__ import annotations

from unittest.mock import MagicMock


from voice_rag_agents.dataflows.retrieval import (
    retrieve,
    assemble_context,
    chunk_to_vector_records,
    _make_chunk_id,
    _make_doc_id,
)
from voice_rag_agents.dataflows.vector_records import SearchResult


def test_make_chunk_id_deterministic() -> None:
    a = _make_chunk_id("hello world", "test.md", 0)
    b = _make_chunk_id("hello world", "test.md", 0)
    assert a == b
    c = _make_chunk_id("different", "test.md", 0)
    assert a != c


def test_make_doc_id_deterministic() -> None:
    assert _make_doc_id("a.md") == _make_doc_id("a.md")
    assert _make_doc_id("a.md") != _make_doc_id("b.md")


def test_assemble_context_empty() -> None:
    context, citations = assemble_context([])
    assert context == ""
    assert citations == []


def test_assemble_context_with_results() -> None:
    results = [
        SearchResult(
            id="vec-1",
            chunk_id="chunk-1",
            chunk_text="API rate limits may impact analytics.",
            score=0.95,
            metadata={"source_file": "meeting_notes.md", "section": "Risks"},
            document_id="doc-1",
        )
    ]
    context, citations = assemble_context(results)
    assert "[S1]" in context
    assert "API rate limits" in context
    assert len(citations) == 1
    assert citations[0].label == "S1"


def test_retrieve_returns_empty_when_no_embedding() -> None:
    mock_emb = MagicMock()
    mock_emb.embed.return_value = MagicMock(vectors=[], model="test", dimension=2048)
    mock_store = MagicMock()
    result = retrieve("test query", mock_emb, mock_store, "collection")
    assert result == []


def test_chunk_to_vector_records_empty() -> None:
    mock_emb = MagicMock()
    records, embeddings = chunk_to_vector_records([], mock_emb)
    assert records == []
    assert embeddings == []
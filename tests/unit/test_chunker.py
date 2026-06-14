"""Unit tests for chunker — no external services required."""

from __future__ import annotations


from voice_rag_agents.dataflows.chunker import chunk_documents, _estimate_tokens


def test_estimate_tokens() -> None:
    assert _estimate_tokens("hello") == 1  # 5 // 4 = 1
    assert _estimate_tokens("a" * 400) == 100


def test_single_chunk_small_text() -> None:
    docs = [{"page_content": "Hello world", "metadata": {"source_file": "test.md"}}]
    chunks = chunk_documents(docs, chunk_size_tokens=500, chunk_overlap_tokens=50)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Hello world"
    assert chunks[0]["chunk_index"] == 0


def test_overlap_produces_multiple_chunks() -> None:
    # 2000 chars ≈ 500 tokens; with 500-token chunks and 75-token overlap
    # we expect multiple chunks
    text = "word " * 500  # ~3000 chars ≈ 750 tokens
    docs = [{"page_content": text, "metadata": {"source_file": "test.md"}}]
    chunks = chunk_documents(docs, chunk_size_tokens=200, chunk_overlap_tokens=50)
    assert len(chunks) >= 2
    # Each chunk should have required keys
    for c in chunks:
        assert "text" in c
        assert "source" in c
        assert "chunk_index" in c
        assert "token_count" in c


def test_empty_documents() -> None:
    assert chunk_documents([]) == []
    assert chunk_documents([{"page_content": "", "metadata": {}}]) == []


def test_metadata_preserved() -> None:
    docs = [{"page_content": "Test content here", "metadata": {"source_file": "doc.md", "section": "intro"}}]
    chunks = chunk_documents(docs, chunk_size_tokens=500, chunk_overlap_tokens=50)
    assert chunks[0]["metadata"]["section"] == "intro"
    assert chunks[0]["source"] == "doc.md"
"""Unit tests for Milvus adapter — skip if pymilvus not installed."""

from __future__ import annotations

import pytest

from voice_rag_agents.dataflows.milvus_adapter import MilvusAdapter

pymilvus = pytest.importorskip("pymilvus", reason="pymilvus not installed")


def test_milvus_import_works() -> None:
    """Verify the adapter class can be imported when pymilvus is available."""
    adapter = MilvusAdapter.__new__(MilvusAdapter)
    assert adapter is not None


def test_milvus_health_without_connection() -> None:
    """Health check returns error status when Milvus is not running."""
    adapter = MilvusAdapter(uri="http://localhost:19530", timeout=2.0)
    result = adapter.health()
    assert result["status"] == "error"
    assert "error" in result


def test_upsert_empty_records() -> None:
    """Upsert with empty records returns 0 without connecting."""
    adapter = MilvusAdapter.__new__(MilvusAdapter)
    adapter._uri = "http://localhost:19530"
    adapter._timeout = 1.0
    adapter._client = None
    result = adapter.upsert("test", [])
    assert result == {"upserted": 0}


def test_delete_by_document_id_returns_error_when_disconnected() -> None:
    """Delete returns error dict when Milvus is not reachable."""
    adapter = MilvusAdapter(uri="http://localhost:19530", timeout=2.0)
    result = adapter.delete_by_document_id("test", "doc-1")
    assert "error" in result

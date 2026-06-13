"""Contract tests: verify mock providers satisfy the interface protocols.

These tests prove that mock implementations conform to the freeze-point
interfaces defined in VRAG-B002, without requiring external services.
"""
from __future__ import annotations

import inspect

import pytest

from voice_rag_agents.model_clients import interfaces as model_ifaces
from voice_rag_agents.model_clients.mock_clients import (
    MockEmbeddingProvider,
    MockLLMProvider,
    MockSTTProvider,
)
from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore
from voice_rag_agents.dataflows.vector_records import SearchRequest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# STT conformance
# ---------------------------------------------------------------------------


def test_mock_stt_has_transcribe():
    """MockSTTProvider exposes transcribe(audio_path) -> STTResult."""
    assert hasattr(MockSTTProvider, "transcribe")
    sig = inspect.signature(MockSTTProvider.transcribe)
    params = list(sig.parameters)
    assert "audio_path" in params


def test_mock_stt_returns_stt_result():
    result = MockSTTProvider().transcribe("fake.wav")
    assert isinstance(result, model_ifaces.STTResult)
    assert isinstance(result.transcript, str)
    assert result.transcript != ""


# ---------------------------------------------------------------------------
# Embedding conformance
# ---------------------------------------------------------------------------


def test_mock_embedding_has_embed():
    """MockEmbeddingProvider exposes embed(request) -> EmbeddingResult."""
    assert hasattr(MockEmbeddingProvider, "embed")
    sig = inspect.signature(MockEmbeddingProvider.embed)
    params = list(sig.parameters)
    assert "request" in params


def test_mock_embedding_returns_embedding_result():
    result = MockEmbeddingProvider(dimension=64).embed(
        model_ifaces.EmbeddingRequest(texts=["hello"])
    )
    assert isinstance(result, model_ifaces.EmbeddingResult)
    assert len(result.vectors) == 1
    assert len(result.vectors[0]) == 64
    assert result.dimension == 64


# ---------------------------------------------------------------------------
# LLM conformance
# ---------------------------------------------------------------------------


def test_mock_llm_has_chat():
    """MockLLMProvider exposes chat(request) -> ChatResult."""
    assert hasattr(MockLLMProvider, "chat")
    sig = inspect.signature(MockLLMProvider.chat)
    params = list(sig.parameters)
    assert "request" in params


def test_mock_llm_returns_chat_result():
    result = MockLLMProvider().chat(
        model_ifaces.ChatRequest(
            messages=[model_ifaces.ChatMessage(role="user", content="hi")]
        )
    )
    assert isinstance(result, model_ifaces.ChatResult)
    assert isinstance(result.content, str)
    assert result.content != ""


# ---------------------------------------------------------------------------
# Vector store conformance
# ---------------------------------------------------------------------------


def test_mock_vector_store_has_required_methods():
    """MockVectorStore exposes all VectorStore protocol methods."""
    required = [
        "health",
        "ensure_collection",
        "upsert",
        "search",
        "delete_by_document_id",
    ]
    for method in required:
        assert hasattr(MockVectorStore, method), f"Missing method: {method}"


def test_mock_vector_store_health_returns_dict():
    result = MockVectorStore().health()
    assert isinstance(result, dict)
    assert "status" in result


def test_mock_vector_store_upsert_returns_dict():
    store = MockVectorStore()
    result = store.upsert("coll", [])
    assert isinstance(result, dict)


def test_mock_vector_store_search_returns_list():
    store = MockVectorStore()
    store.upsert("coll", [])
    req = SearchRequest(query_vector=[1.0, 0.0], top_k=5)
    results = store.search("coll", req)
    assert isinstance(results, list)


def test_mock_vector_store_delete_returns_dict():
    store = MockVectorStore()
    result = store.delete_by_document_id("coll", "doc-1")
    assert isinstance(result, dict)

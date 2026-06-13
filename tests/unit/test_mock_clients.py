"""UT-014 / UT-015 / UT-016 / VRAG-B003: mock provider conformance + determinism."""
from __future__ import annotations

import pytest

from voice_rag_agents.model_clients.interfaces import (
    ChatMessage,
    ChatRequest,
    EmbeddingRequest,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Mock STT
# ---------------------------------------------------------------------------


def test_mock_stt_returns_configured_transcript():
    from voice_rag_agents.model_clients.mock_clients import MockSTTProvider

    stt = MockSTTProvider(transcript="hello world", confidence=0.99)
    result = stt.transcribe("fake.wav")
    assert result.transcript == "hello world"
    assert result.confidence == 0.99
    assert result.provider_metadata["provider"] == "mock"


def test_mock_stt_default_transcript():
    from voice_rag_agents.model_clients.mock_clients import MockSTTProvider

    stt = MockSTTProvider()
    result = stt.transcribe("fake.wav")
    assert result.transcript == "What risks were raised about third-party APIs?"


# ---------------------------------------------------------------------------
# Mock embedding — determinism (UT-014)
# ---------------------------------------------------------------------------


def test_mock_embedding_deterministic():
    """UT-014: same text -> same vector."""
    from voice_rag_agents.model_clients.mock_clients import MockEmbeddingProvider

    provider = MockEmbeddingProvider(dimension=64)
    req = EmbeddingRequest(texts=["hello world"])
    r1 = provider.embed(req)
    r2 = provider.embed(req)
    assert r1.vectors[0] == r2.vectors[0]


def test_mock_embedding_different_texts_differ():
    from voice_rag_agents.model_clients.mock_clients import MockEmbeddingProvider

    provider = MockEmbeddingProvider(dimension=64)
    req = EmbeddingRequest(texts=["hello", "world"])
    result = provider.embed(req)
    assert result.vectors[0] != result.vectors[1]


def test_mock_embedding_dimension():
    """UT-015: configured dimension is respected."""
    from voice_rag_agents.model_clients.mock_clients import MockEmbeddingProvider

    provider = MockEmbeddingProvider(dimension=2048)
    req = EmbeddingRequest(texts=["test"])
    result = provider.embed(req)
    assert len(result.vectors[0]) == 2048
    assert result.dimension == 2048


def test_mock_embedding_dimension_mismatch_error():
    """UT-016: provider returns wrong dimension -> structured error."""
    from voice_rag_agents.agents.schemas import GraphError

    provider_dim = 1024
    expected_dim = 2048
    assert provider_dim != expected_dim
    err = GraphError(
        code="EMBEDDING_DIMENSION_MISMATCH",
        message=f"Embedding dimension {provider_dim} does not match expected {expected_dim}.",
        node="validate_embeddings",
        retryable=False,
        details={"expected": expected_dim, "actual": provider_dim},
    )
    assert err.code == "EMBEDDING_DIMENSION_MISMATCH"
    assert err.details["expected"] == 2048
    assert err.details["actual"] == 1024


def test_mock_embedding_batch_count():
    """Number of vectors equals number of input texts."""
    from voice_rag_agents.model_clients.mock_clients import MockEmbeddingProvider

    provider = MockEmbeddingProvider(dimension=32)
    req = EmbeddingRequest(texts=["a", "b", "c"])
    result = provider.embed(req)
    assert len(result.vectors) == 3


def test_mock_embedding_same_dimension_all_vectors():
    """All vectors in a batch have the same dimension."""
    from voice_rag_agents.model_clients.mock_clients import MockEmbeddingProvider

    provider = MockEmbeddingProvider(dimension=128)
    req = EmbeddingRequest(texts=["x", "y", "z"])
    result = provider.embed(req)
    assert all(len(v) == 128 for v in result.vectors)


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------


def test_mock_llm_no_evidence_response():
    """Mock LLM returns no-evidence response when configured."""
    from voice_rag_agents.model_clients.mock_clients import MockLLMProvider

    llm = MockLLMProvider(no_evidence=True)
    req = ChatRequest(
        messages=[ChatMessage(role="user", content="What is the Q4 budget?")]
    )
    result = llm.chat(req)
    assert "not have enough evidence" in result.content
    assert result.model == "mock-llm"


def test_mock_llm_happy_path_cited():
    """Mock LLM returns cited answer when no_evidence=False."""
    from voice_rag_agents.model_clients.mock_clients import MockLLMProvider

    llm = MockLLMProvider(no_evidence=False)
    req = ChatRequest(
        messages=[ChatMessage(role="user", content="What about risks?")]
    )
    result = llm.chat(req)
    assert "[S1]" in result.content
    assert "risks" in result.content

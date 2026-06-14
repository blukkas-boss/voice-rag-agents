"""Unit tests for embedding adapter — no live HTTP, all mocked."""

from __future__ import annotations

from unittest.mock import patch, MagicMock


from voice_rag_agents.model_clients.embedding_adapter import OpenAIEmbeddingAdapter
from voice_rag_agents.model_clients.interfaces import EmbeddingRequest


def _mock_response(status: int = 200, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.text = "mock"
    return resp


def test_embedding_success() -> None:
    adapter = OpenAIEmbeddingAdapter(
        base_url="http://localhost:8001/v1",
        model="nvidia/llama-nemotron-embed-vl-1b-v2",
        api_key="test-key",
        dimension=2048,
    )
    mock_json = {
        "data": [
            {"index": 0, "embedding": [0.1] * 2048},
            {"index": 1, "embedding": [0.2] * 2048},
        ],
        "model": "nvidia/llama-nemotron-embed-vl-1b-v2",
        "usage": {"prompt_tokens": 10},
    }
    with patch("requests.post", return_value=_mock_response(200, mock_json)):
        result = adapter.embed(EmbeddingRequest(texts=["hello", "world"]))

    assert len(result.vectors) == 2
    assert result.dimension == 2048
    assert result.token_usage is not None


def test_embedding_dimension_mismatch() -> None:
    adapter = OpenAIEmbeddingAdapter(
        base_url="http://localhost:8001/v1",
        model="test",
        dimension=2048,
    )
    mock_json = {
        "data": [{"index": 0, "embedding": [0.1] * 512}],
    }
    with patch("requests.post", return_value=_mock_response(200, mock_json)):
        result = adapter.embed(EmbeddingRequest(texts=["hello"]))

    assert result.vectors == []
    assert "Dimension mismatch" in result.provider_metadata["error"]


def test_embedding_server_error() -> None:
    adapter = OpenAIEmbeddingAdapter(base_url="http://localhost:8001/v1", model="test")
    with patch("requests.post", return_value=_mock_response(500)):
        result = adapter.embed(EmbeddingRequest(texts=["hello"]))

    assert result.vectors == []
    assert "500" in result.provider_metadata["error"]


def test_embedding_timeout() -> None:
    adapter = OpenAIEmbeddingAdapter(base_url="http://localhost:8001/v1", model="test")
    import requests as req

    with patch("requests.post", side_effect=req.Timeout()):
        result = adapter.embed(EmbeddingRequest(texts=["hello"]))

    assert result.vectors == []
    assert "timed out" in result.provider_metadata["error"]
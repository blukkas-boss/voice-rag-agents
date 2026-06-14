"""Unit tests for LLM adapter — no live HTTP, all mocked."""

from __future__ import annotations

from unittest.mock import patch, MagicMock


from voice_rag_agents.model_clients.llm_adapter import OpenAIChatAdapter
from voice_rag_agents.model_clients.interfaces import ChatMessage, ChatRequest


def _mock_response(status: int = 200, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.text = "mock"
    return resp


def test_llm_success() -> None:
    adapter = OpenAIChatAdapter(
        base_url="http://localhost:11434/v1",
        model="llama3.1",
        api_key="ollama",
    )
    mock_json = {
        "choices": [{"message": {"content": "The API risks include rate limits."}}],
        "model": "llama3.1",
        "usage": {"prompt_tokens": 50, "completion_tokens": 20},
    }
    with patch("requests.post", return_value=_mock_response(200, mock_json)):
        result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))

    assert "API risks" in result.content
    assert result.usage is not None


def test_llm_empty_choices() -> None:
    adapter = OpenAIChatAdapter(base_url="http://localhost:11434/v1", model="test")
    with patch("requests.post", return_value=_mock_response(200, {"choices": []})):
        result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))

    assert result.content == ""
    assert "empty choices" in result.provider_metadata["error"]


def test_llm_server_error() -> None:
    adapter = OpenAIChatAdapter(base_url="http://localhost:11434/v1", model="test")
    with patch("requests.post", return_value=_mock_response(500)):
        result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))

    assert result.content == ""
    assert "500" in result.provider_metadata["error"]


def test_llm_timeout() -> None:
    adapter = OpenAIChatAdapter(base_url="http://localhost:11434/v1", model="test")
    import requests as req

    with patch("requests.post", side_effect=req.Timeout()):
        result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))

    assert result.content == ""
    assert "timed out" in result.provider_metadata["error"]
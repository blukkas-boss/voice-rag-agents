"""Contract tests for provider response shapes — no live HTTP."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

from voice_rag_agents.model_clients.interfaces import (
    ChatRequest,
    ChatMessage,
    EmbeddingRequest,
)
from voice_rag_agents.model_clients.embedding_adapter import OpenAIEmbeddingAdapter
from voice_rag_agents.model_clients.llm_adapter import OpenAIChatAdapter
from voice_rag_agents.model_clients.stt_adapter import CommandSTTProvider, HttpSTTProvider


def _mock_response(status: int = 200, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data or {}
    resp.text = "mock"
    return resp


def test_embedding_returns_correct_shape() -> None:
    adapter = OpenAIEmbeddingAdapter(base_url="http://x/v1", model="m", dimension=2048)
    mock_json = {
        "data": [{"index": 0, "embedding": [0.1] * 2048}],
        "model": "m",
    }
    with patch("requests.post", return_value=_mock_response(200, mock_json)):
        result = adapter.embed(EmbeddingRequest(texts=["hello"]))

    assert len(result.vectors) == 1
    assert len(result.vectors[0]) == 2048
    assert result.model == "m"
    assert result.dimension == 2048


def test_llm_returns_correct_shape() -> None:
    adapter = OpenAIChatAdapter(base_url="http://x/v1", model="m")
    mock_json = {
        "choices": [{"message": {"content": "answer"}}],
        "model": "m",
    }
    with patch("requests.post", return_value=_mock_response(200, mock_json)):
        result = adapter.chat(ChatRequest(messages=[ChatMessage(role="user", content="Hi")]))

    assert result.content == "answer"
    assert result.model == "m"


def test_stt_command_returns_correct_shape(tmp_path) -> None:
    fake = tmp_path / "echo.sh"
    fake.write_text('#!/bin/sh\necho "transcribed"\n')
    fake.chmod(0o755)
    provider = CommandSTTProvider(command=[str(fake)])
    result = provider.transcribe(str(tmp_path / "a.wav"))
    assert result.transcript == "transcribed"


def test_stt_http_returns_correct_shape(tmp_path) -> None:
    import responses

    audio_file = tmp_path / "a.wav"
    audio_file.write_bytes(b"fake audio data")
    responses.start()
    responses.add(
        responses.POST,
        "http://x/v1/audio/transcriptions",
        json={"text": "hello", "language": "en", "duration": 1.0},
        status=200,
    )
    provider = HttpSTTProvider(base_url="http://x")
    result = provider.transcribe(str(audio_file))
    assert result.transcript == "hello"
    responses.stop()
    responses.reset()

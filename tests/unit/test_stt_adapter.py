"""Unit tests for STT adapter — no external services required."""

from __future__ import annotations


import pytest

from voice_rag_agents.model_clients.stt_adapter import (
    CommandSTTProvider,
    HttpSTTProvider,
    make_stt_provider,
)
from voice_rag_agents.config import settings


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Ensure settings are re-read for each test."""
    settings.get_settings.cache_clear()
    yield
    settings.get_settings.cache_clear()


def test_command_stt_success(tmp_path) -> None:
    # Create a fake "whisper" that echoes
    fake = tmp_path / "fake_whisper.sh"
    fake.write_text('#!/bin/sh\necho "hello world"\n')
    fake.chmod(0o755)
    provider = CommandSTTProvider(command=[str(fake)], timeout=5)
    result = provider.transcribe(str(tmp_path / "audio.wav"))
    assert result.transcript == "hello world"
    assert result.confidence is None  # command mode doesn't report confidence


def test_command_stt_timeout(tmp_path) -> None:
    fake = tmp_path / "slow.sh"
    fake.write_text('#!/bin/sh\nsleep 10\n')
    fake.chmod(0o755)
    provider = CommandSTTProvider(command=[str(fake)], timeout=0.1)
    result = provider.transcribe(str(tmp_path / "audio.wav"))
    assert result.transcript == ""
    assert result.confidence == 0.0
    assert "timed out" in result.provider_metadata["error"]


def test_command_stt_nonzero_exit(tmp_path) -> None:
    fake = tmp_path / "fail.sh"
    fake.write_text('#!/bin/sh\nexit 1\n')
    fake.chmod(0o755)
    provider = CommandSTTProvider(command=[str(fake)], timeout=5)
    result = provider.transcribe(str(tmp_path / "audio.wav"))
    assert result.transcript == ""
    assert result.confidence == 0.0


def test_command_stt_not_found() -> None:
    provider = CommandSTTProvider(command=["/nonexistent/binary"], timeout=5)
    result = provider.transcribe("/tmp/audio.wav")
    assert result.transcript == ""
    assert "not found" in result.provider_metadata["error"]


def test_http_stt_success(tmp_path) -> None:
    import responses

    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")
    responses.start()
    responses.add(
        responses.POST,
        "http://localhost:9000/v1/audio/transcriptions",
        json={"text": "transcribed text", "language": "en", "duration": 1.5},
        status=200,
    )
    provider = HttpSTTProvider(base_url="http://localhost:9000")
    result = provider.transcribe(str(audio_file))
    assert result.transcript == "transcribed text"
    responses.stop()
    responses.reset()


def test_http_stt_server_error(tmp_path) -> None:
    import responses

    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake audio data")
    responses.start()
    responses.add(
        responses.POST,
        "http://localhost:9000/v1/audio/transcriptions",
        json={"error": "server error"},
        status=500,
    )
    provider = HttpSTTProvider(base_url="http://localhost:9000")
    result = provider.transcribe(str(audio_file))
    assert result.transcript == ""
    assert "500" in result.provider_metadata["error"]
    responses.stop()
    responses.reset()


def test_make_stt_provider_defaults() -> None:
    provider = make_stt_provider(mode="command")
    assert isinstance(provider, CommandSTTProvider)
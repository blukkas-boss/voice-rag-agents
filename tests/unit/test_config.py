"""UT-002 / UT-003 / VRAG-A002: config default load + env override."""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.unit


def test_config_default_load():
    """UT-002: Settings load in mock profile with safe defaults, no .env."""
    # Ensure no VOICE_RAG_ env vars interfere
    for key in list(os.environ):
        if key.startswith("VOICE_RAG_"):
            del os.environ[key]

    from voice_rag_agents.config.settings import reload_settings

    s = reload_settings()
    assert s.profile == "mock"
    assert s.top_k == 5
    assert s.embedding_dim == 2048
    assert s.collection == "voice_rag_chunks"
    assert s.chunk_size_tokens == 500
    assert s.chunk_overlap_tokens == 75
    assert s.stt_provider == "mock"
    assert s.embedding_api_key == ""
    assert s.llm_api_key == ""


def test_config_env_override_top_k():
    """UT-003: VOICE_RAG_TOP_K=8 -> settings.top_k is 8."""
    os.environ["VOICE_RAG_TOP_K"] = "8"
    try:
        from voice_rag_agents.config.settings import reload_settings

        s = reload_settings()
        assert s.top_k == 8
    finally:
        os.environ.pop("VOICE_RAG_TOP_K", None)


def test_config_env_override_top_k_cleanup():
    """UT-003 (repeat after cleanup): ensure default restores."""
    os.environ.pop("VOICE_RAG_TOP_K", None)
    from voice_rag_agents.config.settings import reload_settings

    s = reload_settings()
    assert s.top_k == 5


def test_config_profile_override():
    """Profile can be set via env."""
    os.environ["VOICE_RAG_PROFILE"] = "local"
    try:
        from voice_rag_agents.config.settings import reload_settings

        s = reload_settings()
        assert s.profile == "local"
    finally:
        os.environ["VOICE_RAG_PROFILE"] = "mock"
        from voice_rag_agents.config.settings import reload_settings

        reload_settings()


def test_config_invalid_top_k():
    """Invalid top_k value raises validation error."""
    os.environ["VOICE_RAG_TOP_K"] = "0"
    try:
        from voice_rag_agents.config.settings import reload_settings

        with pytest.raises(Exception):
            reload_settings()
    finally:
        os.environ.pop("VOICE_RAG_TOP_K", None)
        reload_settings()

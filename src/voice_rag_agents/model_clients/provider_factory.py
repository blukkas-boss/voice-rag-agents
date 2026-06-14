"""Provider factory — select mock vs real providers by runtime profile.

Centralizes the profile→provider decision so graph nodes stay clean and the
mock-mode default keeps tests/CI offline. ``profile == "mock"`` returns the
deterministic mocks; any other profile returns the real adapters configured
from settings.
"""

from __future__ import annotations

from voice_rag_agents.config.settings import get_settings

# In mock mode the vector store is in-memory; it must be a process-wide
# singleton so data ingested in one graph run is visible to a later query run
# (and so collection state survives across graph nodes within one run).
_MOCK_VECTOR_STORE = None


def get_stt_provider():
    """Return an STT provider for the current profile."""
    settings = get_settings()
    if settings.is_mock():
        from voice_rag_agents.model_clients.mock_clients import MockSTTProvider

        return MockSTTProvider()
    from voice_rag_agents.model_clients.stt_adapter import make_stt_provider

    return make_stt_provider(
        mode=settings.stt_provider,
        command=settings.stt_command.split() if settings.stt_command else None,
    )


def get_embedding_provider():
    """Return an embedding provider for the current profile."""
    settings = get_settings()
    if settings.is_mock():
        from voice_rag_agents.model_clients.mock_clients import MockEmbeddingProvider

        return MockEmbeddingProvider(dimension=settings.embedding_dim)
    from voice_rag_agents.model_clients.embedding_adapter import OpenAIEmbeddingAdapter

    return OpenAIEmbeddingAdapter(
        base_url=settings.embedding_base_url,
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        dimension=settings.embedding_dim,
    )


def get_llm_provider():
    """Return an LLM provider for the current profile."""
    settings = get_settings()
    if settings.is_mock():
        from voice_rag_agents.model_clients.mock_clients import MockLLMProvider

        return MockLLMProvider(no_evidence=False)
    from voice_rag_agents.model_clients.llm_adapter import OpenAIChatAdapter

    return OpenAIChatAdapter(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
    )


def get_vector_store():
    """Return a vector store for the current profile.

    Mock mode returns a process-wide singleton so ingest/query share state.
    """
    global _MOCK_VECTOR_STORE
    settings = get_settings()
    if settings.is_mock():
        from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

        if _MOCK_VECTOR_STORE is None:
            _MOCK_VECTOR_STORE = MockVectorStore()
        return _MOCK_VECTOR_STORE
    from voice_rag_agents.dataflows.milvus_adapter import MilvusAdapter

    return MilvusAdapter(uri=settings.milvus_uri)


def reset_mock_vector_store() -> None:
    """Clear the singleton mock store (used by tests for isolation)."""
    global _MOCK_VECTOR_STORE
    _MOCK_VECTOR_STORE = None

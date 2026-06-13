"""Pydantic-based settings with env overrides (prefix ``VOICE_RAG_``).

Defaults are taken from :mod:`voice_rag_agents.default_config` so the system
boots without a ``.env`` file and without any secrets.

Usage::

    from voice_rag_agents.config.settings import get_settings
    settings = get_settings()
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

from voice_rag_agents import default_config

# ---------------------------------------------------------------------------
# Profile literal
# ---------------------------------------------------------------------------
Profile = Literal["mock", "local", "integration", "production-local"]

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """Application settings loaded from env with safe defaults.

    Environment variables are read with the prefix ``VOICE_RAG_`` and
    override the built-in defaults.  No ``.env`` file is required.
    """

    model_config = {"env_prefix": "VOICE_RAG_", "env_file": None}

    # -- Runtime -----------------------------------------------------------
    profile: Profile = Field(default_factory=lambda: default_config.PROFILE)

    # -- Retrieval ----------------------------------------------------------
    top_k: int = Field(default_factory=lambda: default_config.TOP_K)
    chunk_size_tokens: int = Field(
        default_factory=lambda: default_config.CHUNK_SIZE_TOKENS
    )
    chunk_overlap_tokens: int = Field(
        default_factory=lambda: default_config.CHUNK_OVERLAP_TOKENS
    )

    # -- Collection --------------------------------------------------------
    collection: str = Field(default_factory=lambda: default_config.COLLECTION)

    # -- Embedding ---------------------------------------------------------
    embedding_base_url: str = Field(
        default_factory=lambda: default_config.EMBEDDING_BASE_URL
    )
    embedding_model: str = Field(
        default_factory=lambda: default_config.EMBEDDING_MODEL
    )
    embedding_dim: int = Field(
        default_factory=lambda: default_config.EMBEDDING_DIM
    )
    embedding_api_key: str = Field(
        default_factory=lambda: default_config.EMBEDDING_API_KEY
    )

    # -- LLM ---------------------------------------------------------------
    llm_base_url: str = Field(
        default_factory=lambda: default_config.LLM_BASE_URL
    )
    llm_model: str = Field(default_factory=lambda: default_config.LLM_MODEL)
    llm_api_key: str = Field(default_factory=lambda: default_config.LLM_API_KEY)

    # -- Milvus ------------------------------------------------------------
    milvus_uri: str = Field(default_factory=lambda: default_config.MILVUS_URI)

    # -- STT ---------------------------------------------------------------
    stt_provider: str = Field(
        default_factory=lambda: default_config.STT_PROVIDER
    )
    stt_command: str = Field(
        default_factory=lambda: default_config.STT_COMMAND
    )
    stt_confidence_threshold: float = Field(
        default_factory=lambda: default_config.STT_CONFIDENCE_THRESHOLD
    )

    # -- Files / safety ----------------------------------------------------
    input_dir: str = Field(default_factory=lambda: default_config.INPUT_DIR)
    max_file_mb: int = Field(
        default_factory=lambda: default_config.MAX_FILE_MB
    )

    # -- Validators --------------------------------------------------------
    @field_validator("top_k")
    @classmethod
    def _top_k_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("top_k must be >= 1")
        return v

    @field_validator("embedding_dim")
    @classmethod
    def _embedding_dim_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("embedding_dim must be >= 1")
        return v

    @field_validator("stt_confidence_threshold")
    @classmethod
    def _stt_conf_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("stt_confidence_threshold must be between 0 and 1")
        return v

    # -- Convenience helpers -----------------------------------------------

    def is_mock(self) -> bool:
        return self.profile == "mock"

    def require_secret(self, field_name: str) -> str:
        """Return a secret or raise a structured error message."""
        value = getattr(self, field_name, "")
        if not value:
            raise ValueError(
                f"Setting '{self.model_config['env_prefix']}{field_name.upper()}' "
                f"is required for profile '{self.profile}' but is empty."
            )
        return value


# ---------------------------------------------------------------------------
# Singleton helper
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (reads env once)."""
    return Settings()


def reload_settings() -> Settings:
    """Clear the cache and re-read env (useful in tests)."""
    get_settings.cache_clear()
    return get_settings()

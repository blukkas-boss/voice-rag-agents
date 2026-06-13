"""Provider interfaces for model clients (STT, embedding, LLM).

These protocols are the *freeze-point* contracts: every real or mock provider
must satisfy them.  Graph nodes depend only on these abstractions.

See ``docs/blueprint/09_MODULE_CONTRACTS_AND_INTERFACES.md`` for the
authoritative contract specification.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# STT
# ---------------------------------------------------------------------------


class STTResult(BaseModel):
    transcript: str
    confidence: float | None = None
    language: str | None = None
    duration_seconds: float | None = None
    provider_metadata: dict = Field(default_factory=dict)


class STTProvider(Protocol):
    """Speech-to-text provider interface."""

    def transcribe(self, audio_path: str) -> STTResult:
        """Transcribe an audio file to text."""
        ...


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


class EmbeddingRequest(BaseModel):
    texts: list[str]
    model: str | None = None
    input_type: Literal["query", "document"] = "document"


class EmbeddingResult(BaseModel):
    vectors: list[list[float]]
    model: str
    dimension: int
    token_usage: dict | None = None
    provider_metadata: dict = Field(default_factory=dict)


class EmbeddingProvider(Protocol):
    """Text embedding provider interface."""

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Embed a batch of texts into vectors."""
        ...


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class ChatResult(BaseModel):
    content: str
    model: str
    usage: dict | None = None
    provider_metadata: dict = Field(default_factory=dict)


class LLMProvider(Protocol):
    """Large-language-model chat provider interface."""

    def chat(self, request: ChatRequest) -> ChatResult:
        """Send a chat request and return the model response."""
        ...

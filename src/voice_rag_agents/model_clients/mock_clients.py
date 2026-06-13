"""Deterministic mock providers for unit and graph tests.

All mocks are fully deterministic, require no external services, and satisfy
the interfaces defined in :mod:`voice_rag_agents.model_clients.interfaces`.
"""

from __future__ import annotations

import hashlib
import math

from voice_rag_agents.model_clients.interfaces import (
    ChatRequest,
    ChatResult,
    EmbeddingRequest,
    EmbeddingResult,
    STTResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text_to_seed(text: str) -> int:
    """Convert text to a stable integer seed via SHA-256."""
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def _seeded_vector(text: str, dimension: int) -> list[float]:
    """Return a deterministic pseudo-random unit vector for *text*.

    Uses a simple LCG seeded by the SHA-256 of the text so the same text
    always produces the same vector.
    """
    seed = _text_to_seed(text)
    # Linear congruential generator parameters (Numerical Recipes)
    a = 1664525
    c = 1013904223
    m = 2**32

    values: list[float] = []
    state = seed % m
    for _ in range(dimension):
        state = (a * state + c) % m
        values.append(state / m)

    # L2-normalise so cosine similarity is just a dot product
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


# ---------------------------------------------------------------------------
# Mock STT
# ---------------------------------------------------------------------------


class MockSTTProvider:
    """Deterministic mock STT provider.

    Returns a configurable transcript.  Useful for graph tests that need a
    predictable transcript without a real audio file.
    """

    def __init__(
        self,
        transcript: str = "What risks were raised about third-party APIs?",
        confidence: float = 0.95,
        language: str = "en",
    ) -> None:
        self._transcript = transcript
        self._confidence = confidence
        self._language = language

    def transcribe(self, audio_path: str) -> STTResult:
        return STTResult(
            transcript=self._transcript,
            confidence=self._confidence,
            language=self._language,
            duration_seconds=1.0,
            provider_metadata={"provider": "mock"},
        )


# ---------------------------------------------------------------------------
# Mock embedding
# ---------------------------------------------------------------------------


class MockEmbeddingProvider:
    """Deterministic mock embedding provider.

    Same text → same vector (via :func:`_seeded_vector`).  Dimension is
    configurable at construction time.
    """

    def __init__(
        self,
        model: str = "mock-embed",
        dimension: int = 2048,
    ) -> None:
        self._model = model
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        vectors = [
            _seeded_vector(text, self._dimension) for text in request.texts
        ]
        return EmbeddingResult(
            vectors=vectors,
            model=request.model or self._model,
            dimension=self._dimension,
            token_usage={"prompt_tokens": 0, "total_tokens": 0},
            provider_metadata={"provider": "mock"},
        )


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------


class MockLLMProvider:
    """Deterministic mock LLM provider.

    When ``no_evidence=True`` (the default) the provider returns a
    no-evidence response regardless of the prompt — this is the grounded
    behaviour the graph expects when retrieval is empty.

    When ``no_evidence=False`` the provider echoes the last user message
    with a fake citation so citation-validation tests can exercise the
    happy path.
    """

    def __init__(
        self,
        model: str = "mock-llm",
        no_evidence: bool = True,
    ) -> None:
        self._model = model
        self._no_evidence = no_evidence

    def chat(self, request: ChatRequest) -> ChatResult:
        if self._no_evidence:
            content = (
                "I do not have enough evidence in the knowledge base "
                "to answer that."
            )
        else:
            # Return a fake cited answer for happy-path tests
            last_user = next(
                (m.content for m in reversed(request.messages) if m.role == "user"),
                "",
            )
            content = (
                f"Based on the retrieved context: {last_user} [S1]"
            )

        return ChatResult(
            content=content,
            model=self._model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            provider_metadata={"provider": "mock"},
        )

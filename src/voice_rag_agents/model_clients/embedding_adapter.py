"""Embedding adapter — OpenAI-compatible /v1/embeddings endpoint.

Satisfies ``voice_rag_agents.model_clients.interfaces.EmbeddingProvider``.
"""

from __future__ import annotations

from voice_rag_agents.model_clients.interfaces import (
    EmbeddingRequest,
    EmbeddingResult,
)


class OpenAIEmbeddingAdapter:
    """Embedding provider via OpenAI-compatible /v1/embeddings API.

    Works with NVIDIA NIM, local embedding proxies, or any OpenAI-compatible
    embeddings endpoint.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        dimension: int = 2048,
        timeout: float = 60.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._dimension = dimension
        self._timeout = timeout

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        import requests

        url = f"{self._base_url}/v1/embeddings"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": request.model or self._model,
            "input": request.texts,
        }

        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=self._timeout
            )
        except requests.Timeout:
            return EmbeddingResult(
                vectors=[],
                model=self._model,
                dimension=self._dimension,
                provider_metadata={"error": f"Embedding request timed out after {self._timeout}s"},
            )
        except Exception as exc:  # noqa: BLE001
            return EmbeddingResult(
                vectors=[],
                model=self._model,
                dimension=self._dimension,
                provider_metadata={"error": str(exc)[:200]},
            )

        if resp.status_code != 200:
            return EmbeddingResult(
                vectors=[],
                model=self._model,
                dimension=self._dimension,
                provider_metadata={
                    "error": f"Embedding API returned {resp.status_code}: {resp.text[:200]}"
                },
            )

        try:
            data = resp.json()
        except ValueError:
            return EmbeddingResult(
                vectors=[],
                model=self._model,
                dimension=self._dimension,
                provider_metadata={"error": "Embedding API returned non-JSON response"},
            )

        vectors: list[list[float]] = []
        for item in sorted(data.get("data", []), key=lambda x: x.get("index", 0)):
            vec = item.get("embedding", [])
            if len(vec) != self._dimension:
                return EmbeddingResult(
                    vectors=[],
                    model=self._model,
                    dimension=self._dimension,
                    provider_metadata={
                        "error": f"Dimension mismatch: expected {self._dimension}, got {len(vec)}"
                    },
                )
            vectors.append(vec)

        usage = data.get("usage", {})
        return EmbeddingResult(
            vectors=vectors,
            model=data.get("model", self._model),
            dimension=self._dimension,
            token_usage=usage if usage else None,
            provider_metadata={"provider": "openai-compat"},
        )

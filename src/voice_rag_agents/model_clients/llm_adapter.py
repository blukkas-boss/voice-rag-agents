"""LLM adapter — OpenAI-compatible /v1/chat/completions endpoint.

Satisfies ``voice_rag_agents.model_clients.interfaces.LLMProvider``.
"""

from __future__ import annotations

from voice_rag_agents.model_clients.interfaces import (
    ChatRequest,
    ChatResult,
)


class OpenAIChatAdapter:
    """LLM provider via OpenAI-compatible /v1/chat/completions API.

    Works with Ollama, NVIDIA NIM, or any OpenAI-compatible chat endpoint.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    def chat(self, request: ChatRequest) -> ChatResult:
        import requests

        url = f"{self._base_url}/v1/chat/completions"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict = {
            "model": request.model or self._model,
            "messages": [m.model_dump() for m in request.messages],
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        try:
            resp = requests.post(
                url, json=payload, headers=headers, timeout=self._timeout
            )
        except requests.Timeout:
            return ChatResult(
                content="",
                model=self._model,
                provider_metadata={"error": f"LLM request timed out after {self._timeout}s"},
            )
        except Exception as exc:  # noqa: BLE001
            return ChatResult(
                content="",
                model=self._model,
                provider_metadata={"error": str(exc)[:200]},
            )

        if resp.status_code != 200:
            return ChatResult(
                content="",
                model=self._model,
                provider_metadata={
                    "error": f"LLM API returned {resp.status_code}: {resp.text[:200]}"
                },
            )

        try:
            data = resp.json()
        except ValueError:
            return ChatResult(
                content="",
                model=self._model,
                provider_metadata={"error": "LLM API returned non-JSON response"},
            )

        choices = data.get("choices", [])
        if not choices:
            return ChatResult(
                content="",
                model=self._model,
                provider_metadata={"error": "LLM API returned empty choices"},
            )

        message = choices[0].get("message", {})
        content = message.get("content", "")

        usage = data.get("usage", {})
        return ChatResult(
            content=content,
            model=data.get("model", self._model),
            usage=usage if usage else None,
            provider_metadata={"provider": "openai-compat"},
        )

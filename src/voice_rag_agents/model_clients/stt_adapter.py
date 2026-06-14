"""STT adapter — speech-to-text provider implementations.

Two modes:
- ``command``: run a local binary (e.g. whisper.cpp) as a subprocess.
- ``http``: POST audio to an HTTP STT endpoint (Whisper-compatible).

Both satisfy ``voice_rag_agents.model_clients.interfaces.STTProvider``.
"""

from __future__ import annotations

import subprocess

from voice_rag_agents.model_clients.interfaces import STTProvider, STTResult


class CommandSTTProvider:
    """STT via a local binary invoked as a subprocess."""

    def __init__(self, command: list[str], timeout: float = 60.0) -> None:
        self._command = command
        self._timeout = timeout

    def transcribe(self, audio_path: str) -> STTResult:
        cmd = [*self._command, audio_path]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except FileNotFoundError:
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={"error": f"command not found: {self._command[0]}"},
            )
        except subprocess.TimeoutExpired:
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={"error": f"STT command timed out after {self._timeout}s"},
            )

        if result.returncode != 0:
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={
                    "error": f"STT command exited {result.returncode}: {result.stderr[:200]}"
                },
            )

        return STTResult(
            transcript=result.stdout.strip(),
            confidence=None,  # command-mode doesn't report confidence
            provider_metadata={"provider": "command"},
        )


class HttpSTTProvider:
    """STT via an HTTP endpoint (Whisper-compatible /v1/audio/transcriptions)."""

    def __init__(self, base_url: str, api_key: str = "", timeout: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def transcribe(self, audio_path: str) -> STTResult:
        import requests

        url = f"{self._base_url}/v1/audio/transcriptions"
        headers: dict[str, str] = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            with open(audio_path, "rb") as fh:
                resp = requests.post(
                    url,
                    files={"file": fh},
                    headers=headers,
                    timeout=self._timeout,
                )
        except requests.Timeout:
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={"error": f"HTTP STT timed out after {self._timeout}s"},
            )
        except Exception as exc:  # noqa: BLE001
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={"error": str(exc)[:200]},
            )

        if resp.status_code != 200:
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={
                    "error": f"HTTP STT returned {resp.status_code}: {resp.text[:200]}"
                },
            )

        try:
            data = resp.json()
        except ValueError:
            return STTResult(
                transcript="",
                confidence=0.0,
                provider_metadata={"error": "HTTP STT returned non-JSON response"},
            )

        return STTResult(
            transcript=data.get("text", ""),
            confidence=None,
            language=data.get("language"),
            duration_seconds=data.get("duration"),
            provider_metadata={"provider": "http"},
        )


# Registry: provider name -> factory
def make_stt_provider(
    mode: str = "command",
    command: list[str] | None = None,
    http_url: str = "",
    http_key: str = "",
    timeout: float = 60.0,
) -> STTProvider:
    """Build an STT provider by mode string.

    ``settings.stt_provider`` drives the default mode.
    """
    if mode == "http":
        return HttpSTTProvider(base_url=http_url, api_key=http_key, timeout=timeout)
    return CommandSTTProvider(command=command or [], timeout=timeout)

"""FastAPI service exposing the voice_rag_agents pipeline.

Endpoints (per 05_ORCHESTRATION_PLAN single-product assembly):
- POST /ingest    — ingest documents through the IngestionGraph
- POST /query     — answer a question through the QueryGraph
- POST /eval/run  — run a golden evaluation batch
- GET  /health    — service + provider health

Runs in mock profile by default (no external services). The graph layer
selects mock vs real providers based on settings.profile.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


from fastapi import Request, Response
from pydantic import BaseModel, Field

from voice_rag_agents.config.settings import get_settings
from voice_rag_agents.graph.states import VoiceRAGState


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class IngestRequest(BaseModel):
    documents: list[dict] = Field(default_factory=list)
    path: str | None = None


class IngestResponse(BaseModel):
    run_id: str
    status: str
    report: dict = Field(default_factory=dict)


class QueryRequest(BaseModel):
    question: str | None = None
    audio_path: str | None = None
    top_k: int | None = None
    filters: dict | None = None


class QueryResponse(BaseModel):
    run_id: str
    answer: str
    citations: list[dict] = Field(default_factory=list)
    final_status: str = "success"


class EvalRunRequest(BaseModel):
    dataset: str = "golden"


class EvalRunResponse(BaseModel):
    run_id: str
    status: str
    metrics: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    profile: str
    timestamp: str
    providers: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# OpenAI-compatible models (for Open WebUI integration)
# ---------------------------------------------------------------------------


class OAIMessage(BaseModel):
    role: str
    content: str


class OAIChatRequest(BaseModel):
    model: str = ""
    messages: list[OAIMessage] = Field(default_factory=list)
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


class OAIChoice(BaseModel):
    index: int = 0
    message: OAIMessage
    finish_reason: str = "stop"


class OAIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OAIChatResponse(BaseModel):
    id: str = ""
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: list[OAIChoice] = Field(default_factory=list)
    usage: OAIUsage = Field(default_factory=OAIUsage)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_run_id() -> str:
    return f"run-{uuid.uuid4().hex[:12]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_state(request_type: str, run_id: str) -> VoiceRAGState:
    settings = get_settings()
    return {
        "run_id": run_id,
        "request_type": request_type,  # type: ignore[typeddict-item]
        "user_id": "api",
        "session_id": run_id,
        "created_at": _now(),
        "runtime_profile": settings.profile,
    }


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app():
    """Create and configure the FastAPI application."""
    from fastapi import FastAPI, HTTPException

    app = FastAPI(
        title="voice_rag_agents",
        version="0.0.1",
        description="Local-first voice-to-answer RAG product.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        settings = get_settings()
        return HealthResponse(
            status="ok",
            profile=settings.profile,
            timestamp=_now(),
            providers={
                "embedding": settings.embedding_model,
                "llm": settings.llm_model,
                "vector_store": "milvus" if settings.profile != "mock" else "mock",
                "stt": settings.stt_provider,
            },
        )

    @app.post("/ingest", response_model=IngestResponse)
    def ingest(req: IngestRequest) -> IngestResponse:
        from voice_rag_agents.graph.ingestion_graph import run_ingestion_graph

        run_id = _new_run_id()
        state = _base_state("ingest", run_id)
        state["input_documents"] = req.documents

        try:
            result = run_ingestion_graph(state)
        except Exception as exc:  # noqa: BLE001 — surface as 500 with safe message
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")

        report = result.get("ingestion_report", {})
        return IngestResponse(
            run_id=run_id,
            status=report.get("status", "unknown"),
            report=report,
        )

    @app.post("/query", response_model=QueryResponse)
    def query(req: QueryRequest) -> QueryResponse:
        from voice_rag_agents.graph.query_graph import run_query_graph

        if not req.question and not req.audio_path:
            raise HTTPException(status_code=400, detail="question or audio_path required")

        run_id = _new_run_id()
        state = _base_state("query", run_id)
        if req.question:
            state["input_text"] = req.question
        if req.audio_path:
            state["input_audio_path"] = req.audio_path

        try:
            result = run_query_graph(state, config={"recursion_limit": 50})
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

        return QueryResponse(
            run_id=run_id,
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            final_status=result.get("final_status", "success"),
        )

    @app.post("/eval/run", response_model=EvalRunResponse)
    def eval_run(req: EvalRunRequest) -> EvalRunResponse:
        run_id = _new_run_id()
        # Eval runner is wired in Wave 5 (testing workforce). Return a
        # structured stub so the endpoint contract is stable now.
        return EvalRunResponse(
            run_id=run_id,
            status="not_implemented",
            metrics={"note": "RAG eval runner lands in Wave 5"},
        )

    # ------------------------------------------------------------------
    # OpenAI-compatible endpoint — Open WebUI integration (Option D)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Ollama-compatible proxy endpoints — Open WebUI model discovery
    # ------------------------------------------------------------------

    @app.get("/api/tags")
    def ollama_tags():
        """Return the Ollama model list plus our RAG model for Open WebUI discovery."""
        import httpx
        settings = get_settings()
        ollama_url = settings.llm_base_url.rsplit("/v1", 1)[0]
        try:
            r = httpx.get(f"{ollama_url}/api/tags", timeout=10)
            data = r.json()
        except Exception:
            data = {"models": []}
        # Inject our RAG model so Open WebUI discovers it alongside Ollama models
        data["models"].append(
            {
                "name": "rag-api:latest",
                "model": "rag-api:latest",
                "modified_at": datetime.now(timezone.utc).isoformat(),
                "size": 0,
                "digest": "rag",
                "details": {
                    "parent_model": "",
                    "format": "rag",
                    "family": "rag",
                    "families": ["rag"],
                    "parameter_size": "0",
                    "quantization_level": "none",
                    "context_length": 131072,
                    "embedding_length": 768,
                },
            }
        )
        return data

    @app.get("/api/version")
    def ollama_version():
        """Return Ollama version for Open WebUI compatibility."""
        import httpx
        settings = get_settings()
        ollama_url = settings.llm_base_url.rsplit("/v1", 1)[0]
        try:
            r = httpx.get(f"{ollama_url}/api/version", timeout=10)
            return r.json()
        except Exception:
            return {"version": "0.30.8"}

    @app.get("/models")
    def list_models_root():
        """OpenAI-compatible model listing at the no-prefix path.

        Open WebUI calls {base_url}/models (without /v1) when discovering
        models for an OpenAI-style backend. Returning the model list here
        prevents this GET from falling through to the POST /api/chat
        handler (which would try to parse an empty body and 500).
        """
        settings = get_settings()
        return {
            "object": "list",
            "data": [
                {
                    "id": "rag-api",
                    "object": "model",
                    "created": 0,
                    "owned_by": "voice_rag_agents",
                },
                {
                    "id": settings.llm_model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "ollama",
                },
            ],
        }

    # ------------------------------------------------------------------
    # Ollama /api/chat proxy — intercepts rag-api, proxies rest to Ollama
    # ------------------------------------------------------------------

    @app.post("/api/chat")
    async def ollama_chat(request: Request):
        """Handle Ollama /api/chat — RAG for rag-api, proxy for everything else."""
        import httpx
        body = await request.json()
        model = body.get("model", "")
        settings = get_settings()
        ollama_url = settings.llm_base_url.rsplit("/v1", 1)[0]

        # If the model is our RAG model, run the full RAG pipeline.
        # Open WebUI may send it with or without the :latest tag.
        if model in ("rag-api", "rag-api:latest"):
            return await _handle_rag_chat(body)

        # Otherwise, proxy to the real Ollama
        try:
            r = httpx.post(
                f"{ollama_url}/api/chat",
                json=body,
                timeout=300,
            )
            return Response(content=r.text, media_type="application/json")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Ollama proxy error: {exc}")

    async def _handle_rag_chat(body: dict):
        """Run the RAG pipeline and return in Ollama /api/chat format."""
        from voice_rag_agents.graph.query_graph import run_query_graph

        messages = body.get("messages", [])
        user_messages = [m.get("content", "") for m in messages if m.get("role") == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        question = user_messages[-1]

        run_id = _new_run_id()
        state = _base_state("query", run_id)
        state["input_text"] = question

        try:
            result = run_query_graph(state, config={"recursion_limit": 50})
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

        answer = result.get("answer", "")
        now = datetime.now(timezone.utc).isoformat()

        return {
            "model": "rag-api",
            "created_at": now,
            "message": {"role": "assistant", "content": answer},
            "done": True,
            "done_reason": "stop",
        }

    @app.get("/v1/models")
    def list_models():
        """OpenAI-compatible model listing for Open WebUI.
        Open WebUI calls {base_url}/models (no /v1 prefix) when discovering
        OpenAI backend models, so we serve this at both paths.
        """
        settings = get_settings()
        return {
            "object": "list",
            "data": [
                {
                    "id": "rag-api",
                    "object": "model",
                    "created": 0,
                    "owned_by": "voice_rag_agents",
                },
                {
                    "id": settings.llm_model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "ollama",
                },
            ],
        }

    @app.post("/v1/chat/completions", response_model=OAIChatResponse)
    def chat_completions(req: OAIChatRequest) -> OAIChatResponse:
        """OpenAI-compatible chat completions that runs the full RAG pipeline.

        Open WebUI hits this endpoint as if it were Ollama /v1/chat/completions.
        We extract the latest user message, run it through the QueryGraph
        (embed → retrieve from Milvus → generate grounded answer), and
        return the result shaped like an OpenAI response.
        """
        from voice_rag_agents.graph.query_graph import run_query_graph

        # Extract the user's question from the messages
        user_messages = [m.content for m in req.messages if m.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        question = user_messages[-1]

        run_id = _new_run_id()
        state = _base_state("query", run_id)
        state["input_text"] = question

        try:
            result = run_query_graph(state, config={"recursion_limit": 50})
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

        answer = result.get("answer", "")
        settings = get_settings()

        return OAIChatResponse(
            id=run_id,
            created=int(datetime.now(timezone.utc).timestamp()),
            model=req.model or settings.llm_model,
            choices=[
                OAIChoice(
                    message=OAIMessage(role="assistant", content=answer),
                )
            ],
        )

    return app


# Module-level app for `uvicorn voice_rag_agents.service.api:app`
app = create_app()

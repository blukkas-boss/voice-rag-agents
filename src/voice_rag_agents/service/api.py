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
            result = run_query_graph(state)
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

    return app


# Module-level app for `uvicorn voice_rag_agents.service.api:app`
app = create_app()

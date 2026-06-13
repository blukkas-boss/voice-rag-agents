"""LangGraph state models.

Defines the typed state that flows through every graph and subgraph, plus
lightweight SearchResult used by retrieval nodes.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from voice_rag_agents.agents.schemas import (
    ChunkRecord,
    Citation,
    DocumentRecord,
    EmbeddingRecord,
    GraphError,
)
from voice_rag_agents.dataflows.vector_records import VectorRecord


# Re-export SearchResult from its canonical home so existing imports keep working.
from voice_rag_agents.dataflows.vector_records import SearchResult  # noqa: F401


class VoiceRAGState(TypedDict, total=False):
    """Top-level state passed between supervisor and subgraphs.

    Fields are optional (``total=False``) so each graph only touches the
    keys it needs.  See ``02_LANGGRAPH_PRODUCT_ARCHITECTURE.md`` for the
    full field catalogue.
    """

    # -- Identity ----------------------------------------------------------
    run_id: str
    request_type: Literal["ingest", "query", "admin", "eval"]
    user_id: str
    session_id: str
    created_at: str
    runtime_profile: str

    # -- Inputs ------------------------------------------------------------
    input_text: str | None
    input_audio_path: str | None
    input_documents: list[dict]
    command: str | None

    # -- Speech ------------------------------------------------------------
    transcript: str | None
    stt_confidence: float | None

    # -- Ingestion ---------------------------------------------------------
    documents: list[DocumentRecord]
    chunks: list[ChunkRecord]
    embeddings: list[EmbeddingRecord]
    vector_records: list[VectorRecord]
    ingestion_report: dict

    # -- Query -------------------------------------------------------------
    normalized_query: str
    rewritten_query: str | None
    query_embedding: list[float]
    retrieval_results: list[SearchResult]
    assembled_context: str

    # -- Answer ------------------------------------------------------------
    answer: str
    citations: list[Citation]
    answer_quality: dict

    # -- Control -----------------------------------------------------------
    errors: list[GraphError]
    warnings: list[str]
    retries: dict[str, int]
    human_actions_required: list[str]
    final_status: Literal["success", "partial", "failed"]

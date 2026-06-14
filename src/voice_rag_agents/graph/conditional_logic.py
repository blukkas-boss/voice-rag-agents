"""Conditional routing functions for LangGraph edges.

Pure functions that inspect VoiceRAGState and return the next node name
or special constants like END. No side effects.
"""

from __future__ import annotations

from typing import Literal

from voice_rag_agents.config.settings import get_settings
from voice_rag_agents.graph.states import VoiceRAGState


# ---------------------------------------------------------------------------
# Supervisor routing
# ---------------------------------------------------------------------------


def route_request_type(state: VoiceRAGState) -> Literal[
    "ingestion_subgraph",
    "query_subgraph", 
    "admin_subgraph",
    "evaluation_subgraph",
    "handle_error",
    "__end__"
]:
    """Route to subgraph based on request_type field.
    
    Returns:
        One of: ingestion_subgraph, query_subgraph, admin_subgraph, 
                evaluation_subgraph, handle_error, or __end__
    """
    request_type = state.get("request_type")
    
    if request_type == "ingest":
        return "ingestion_subgraph"
    elif request_type == "query":
        return "query_subgraph"
    elif request_type == "admin":
        return "admin_subgraph"
    elif request_type == "eval":
        return "evaluation_subgraph"
    elif request_type is None or request_type not in ["ingest", "query", "admin", "eval"]:
        return "handle_error"
    
    return "__end__"


# ---------------------------------------------------------------------------
# QueryGraph routing
# ---------------------------------------------------------------------------


def query_input_route(state: VoiceRAGState) -> Literal["voice", "text", "error"]:
    """Route based on input type for query processing.
    
    Returns:
        "voice" if input_audio_path is present,
        "text" if input_text is present,
        "error" otherwise
    """
    if state.get("input_audio_path"):
        return "voice"
    elif state.get("input_text"):
        return "text"
    else:
        return "error"


def retrieval_route(state: VoiceRAGState) -> Literal["has_results", "no_results", "error"]:
    """Route based on retrieval results.
    
    Returns:
        "has_results" if retrieval_results is non-empty list,
        "no_results" if retrieval_results is empty list,
        "error" if errors are present in state
    """
    errors = state.get("errors", [])
    if errors:
        return "error"
    
    retrieval_results = state.get("retrieval_results", [])
    if retrieval_results:
        return "has_results"
    else:
        return "no_results"


def citation_route(state: VoiceRAGState) -> Literal["valid", "retry", "invalid"]:
    """Route based on citation validation.
    
    Returns:
        "valid" if citations are present and valid,
        "retry" if retry_count < 1 (allow one retry),
        "invalid" otherwise (no retry left or validation failed)
    """
    # Check if citations validation passed
    citations = state.get("citations", [])
    answer = state.get("answer", "")
    
    # Simple validation: check if we have citations and answer mentions them
    # In a real implementation, this would use the CitationValidator
    has_citations = len(citations) > 0 and answer and "[S" in answer
    
    if has_citations:
        return "valid"
    
    # Check retry count
    retries = state.get("retries", {})
    citation_retries = retries.get("citation_validation", 0)
    
    if citation_retries < 1:
        return "retry"
    else:
        return "invalid"


def stt_confidence_route(state: VoiceRAGState) -> Literal["acceptable", "low"]:
    """Route based on STT confidence vs threshold.
    
    Returns:
        "acceptable" if stt_confidence >= threshold from config,
        "low" otherwise
    """
    settings = get_settings()
    threshold = settings.stt_confidence_threshold
    confidence = state.get("stt_confidence")
    
    if confidence is None:
        # No confidence score available, treat as low
        return "low"
    
    return "acceptable" if confidence >= threshold else "low"


# ---------------------------------------------------------------------------
# IngestionGraph routing
# ---------------------------------------------------------------------------


def parse_error_route(state: VoiceRAGState) -> Literal["quarantine", "normalize"]:
    """Route based on parsing success.
    
    Returns:
        "quarantine" if errors are present from parsing,
        "normalize" otherwise
    """
    errors = state.get("errors", [])
    # Check if any errors are from parsing stage
    parse_errors = [e for e in errors if e.get("node") == "parse_documents"]
    
    if parse_errors:
        return "quarantine"
    else:
        return "normalize"


def embedding_retry_route(state: VoiceRAGState) -> Literal["retry", "validate", "error"]:
    """Route based on embedding success and retry count.
    
    Returns:
        "retry" if embedding failed and retries < 2,
        "validate" if embedding succeeded,
        "error" if embedding failed and retries >= 2
    """
    errors = state.get("errors", [])
    embedding_errors = [e for e in errors if e.get("node") == "embed_chunks"]
    
    if not embedding_errors:
        return "validate"
    
    retries = state.get("retries", {})
    embed_retries = retries.get("embed_chunks", 0)
    
    if embed_retries < 2:
        return "retry"
    else:
        return "error"


def dimension_mismatch_route(state: VoiceRAGState) -> Literal["upsert", "error"]:
    """Route based on embedding dimension validation.
    
    Returns:
        "upsert" if dimensions match,
        "error" if dimensions mismatch
    """
    errors = state.get("errors", [])
    dim_errors = [e for e in errors if e.get("code") == "EMBEDDING_DIMENSION_MISMATCH"]
    
    if dim_errors:
        return "error"
    else:
        return "upsert"


def ingestion_retry_route(state: VoiceRAGState) -> Literal["retry", "verify", "error"]:
    """Route based on upsert success and retry count.
    
    Returns:
        "retry" if upsert failed and retries < 2,
        "verify" if upsert succeeded,
        "error" if upsert failed and retries >= 2
    """
    errors = state.get("errors", [])
    upsert_errors = [e for e in errors if e.get("node") == "upsert_records"]
    
    if not upsert_errors:
        return "verify"
    
    retries = state.get("retries", {})
    upsert_retries = retries.get("upsert_records", 0)
    
    if upsert_retries < 2:
        return "retry"
    else:
        return "error"
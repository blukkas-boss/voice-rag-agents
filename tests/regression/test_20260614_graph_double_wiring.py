"""Regression: double-wired edges caused nodes to run twice / drop state, and
malformed nested-list error returns broke citation validation.

Bug summary (Wave 4):
1. Both `add_edge` (direct) AND `add_conditional_edges` existed for the same
   source nodes in the ingestion and query graphs. The duplicate path made nodes
   execute twice and dropped state on the fan-in, so a valid retrieval still
   produced a `CITATION_VALIDATION_FAILED` error.
2. `validate_citations`/`validate_groundedness` returned
   `[state.get("errors", []) + [error]]` — a nested list `[[...]]` — corrupting
   the error channel.

Failure before fix: a normal text query 500'd with CITATION_VALIDATION_FAILED
even though one citation was retrieved.
Expected after fix: a normal text query returns an answer with >= 1 citation and
no errors; each node runs once.
"""

from __future__ import annotations

import pytest

from voice_rag_agents.graph.ingestion_graph import run_ingestion_graph
from voice_rag_agents.graph.query_graph import build_query_graph, run_query_graph
from voice_rag_agents.model_clients.provider_factory import reset_mock_vector_store


@pytest.fixture(autouse=True)
def _clean():
    reset_mock_vector_store()
    yield
    reset_mock_vector_store()


def _seed() -> None:
    run_ingestion_graph(
        {
            "run_id": "reg-i",
            "request_type": "ingest",
            "user_id": "u",
            "session_id": "s",
            "runtime_profile": "mock",
            "input_documents": [
                {"text": "API rate limits may impact analytics.", "source_file": "m.md"}
            ],
        }
    )


def test_query_returns_cited_answer_without_errors() -> None:
    _seed()
    out = run_query_graph(
        {
            "run_id": "reg-q",
            "request_type": "query",
            "user_id": "u",
            "session_id": "s",
            "runtime_profile": "mock",
            "input_text": "What are the API risks?",
        }
    )
    assert not out.get("errors"), out.get("errors")
    assert out.get("citations"), "expected at least one citation"
    assert "error while processing" not in (out.get("answer", "") or "").lower()


def test_each_node_runs_once_no_double_wiring() -> None:
    _seed()
    graph = build_query_graph()
    counts: dict[str, int] = {}
    for step in graph.stream(
        {
            "run_id": "reg-q2",
            "request_type": "query",
            "user_id": "u",
            "session_id": "s",
            "runtime_profile": "mock",
            "input_text": "What are the API risks?",
        },
        {"recursion_limit": 30},
        stream_mode="updates",
    ):
        for node in step:
            counts[node] = counts.get(node, 0) + 1
    doubled = {n: c for n, c in counts.items() if c > 1}
    assert not doubled, f"nodes executed more than once (double-wiring): {doubled}"

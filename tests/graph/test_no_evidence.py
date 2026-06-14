"""GT-005 — QueryGraph no-evidence fallback on empty retrieval.

When the vector store returns no results, the query graph must route to the
no-evidence response rather than fabricating an answer (guardrail 7: no
unsupported answers on retrieval failure).
"""

from __future__ import annotations

import pytest

from voice_rag_agents.graph.query_graph import run_query_graph
from voice_rag_agents.model_clients.provider_factory import reset_mock_vector_store

pytestmark = pytest.mark.graph


@pytest.fixture(autouse=True)
def _clean():
    reset_mock_vector_store()
    yield
    reset_mock_vector_store()


def test_gt005_no_evidence_on_empty_store() -> None:
    # No ingestion -> empty vector store -> empty retrieval.
    out = run_query_graph(
        {
            "run_id": "gt005",
            "request_type": "query",
            "user_id": "u",
            "session_id": "s",
            "runtime_profile": "mock",
            "input_text": "What was decided about the budget?",
        }
    )
    answer = (out.get("answer") or "").lower()
    assert "do not have enough evidence" in answer
    assert not out.get("citations")

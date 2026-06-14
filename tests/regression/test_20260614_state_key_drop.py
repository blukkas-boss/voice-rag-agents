"""Regression: langgraph dropped undeclared state keys between supersteps.

Bug summary (Wave 4): `ingestion_graph` wrote `upsert_result` / `collection_name`
/ `dimension` as state updates, but those keys are NOT declared channels in the
`VoiceRAGState` TypedDict. LangGraph silently drops undeclared keys between
supersteps, so `write_ingestion_report` saw an empty `upsert_result` and reported
`records_upserted: 0` / `status: failed` even though upsert succeeded.

Failure before fix: ingestion always reported `failed` with 0 records upserted.
Expected after fix: ingest of a valid document reports `success` with
`records_upserted >= 1` (count flows via the declared `ingestion_report` channel).
"""

from __future__ import annotations

import pytest

from voice_rag_agents.graph.ingestion_graph import run_ingestion_graph
from voice_rag_agents.model_clients.provider_factory import reset_mock_vector_store


@pytest.fixture(autouse=True)
def _clean():
    reset_mock_vector_store()
    yield
    reset_mock_vector_store()


def test_ingestion_reports_success_with_upserted_count() -> None:
    result = run_ingestion_graph(
        {
            "run_id": "reg-ingest",
            "request_type": "ingest",
            "user_id": "u",
            "session_id": "s",
            "runtime_profile": "mock",
            "input_documents": [
                {
                    "text": "API rate limits may impact analytics. Bob owns mitigation.",
                    "source_file": "m.md",
                }
            ],
        }
    )
    report = result.get("ingestion_report") or {}
    assert report.get("status") == "success", report
    assert report.get("records_upserted", 0) >= 1, report

"""Performance smoke tests (PERF-001..003).

Generous CI-safe thresholds — these catch pathological regressions, not micro
latency. Mock profile, no external services. PERF-004 (Milvus) is integration.
"""

from __future__ import annotations

import time

import pytest

from voice_rag_agents.graph.ingestion_graph import run_ingestion_graph
from voice_rag_agents.graph.query_graph import run_query_graph
from voice_rag_agents.model_clients.provider_factory import (
    get_vector_store,
    reset_mock_vector_store,
)

pytestmark = pytest.mark.performance

QUERY_BUDGET_S = 2.0
INGEST_BUDGET_S = 2.0
RETRIEVAL_1K_BUDGET_S = 3.0


@pytest.fixture(autouse=True)
def _clean():
    reset_mock_vector_store()
    yield
    reset_mock_vector_store()


def _ingest_one() -> None:
    run_ingestion_graph(
        {
            "run_id": "perf-ingest",
            "request_type": "ingest",
            "user_id": "p",
            "session_id": "p",
            "runtime_profile": "mock",
            "input_documents": [
                {"text": "API rate limits may impact analytics.", "source_file": "m.md"}
            ],
        }
    )


def test_perf_001_mock_query_latency() -> None:
    _ingest_one()
    start = time.perf_counter()
    run_query_graph(
        {
            "run_id": "perf-q",
            "request_type": "query",
            "user_id": "p",
            "session_id": "p",
            "runtime_profile": "mock",
            "input_text": "What are the API risks?",
        }
    )
    elapsed = time.perf_counter() - start
    assert elapsed < QUERY_BUDGET_S, f"query took {elapsed:.3f}s (budget {QUERY_BUDGET_S}s)"


def test_perf_002_small_ingestion_latency() -> None:
    start = time.perf_counter()
    _ingest_one()
    elapsed = time.perf_counter() - start
    assert elapsed < INGEST_BUDGET_S, f"ingest took {elapsed:.3f}s (budget {INGEST_BUDGET_S}s)"


def test_perf_003_retrieval_latency_1000_records() -> None:
    from voice_rag_agents.dataflows.vector_records import VectorRecord

    store = get_vector_store()
    store.ensure_collection("voice_rag_chunks", 2048)
    records = [
        VectorRecord(
            id=f"vec-{i}",
            document_id=f"doc-{i}",
            chunk_id=f"chunk-{i}",
            chunk_text=f"record number {i} about analytics and API limits",
            vector=[float((i % 7) + 1)] * 8,
            metadata={"i": i},
        )
        for i in range(1000)
    ]
    store.upsert("voice_rag_chunks", records)

    start = time.perf_counter()
    run_query_graph(
        {
            "run_id": "perf-1k",
            "request_type": "query",
            "user_id": "p",
            "session_id": "p",
            "runtime_profile": "mock",
            "input_text": "analytics API limits",
        }
    )
    elapsed = time.perf_counter() - start
    assert elapsed < RETRIEVAL_1K_BUDGET_S, (
        f"retrieval over 1k took {elapsed:.3f}s (budget {RETRIEVAL_1K_BUDGET_S}s)"
    )

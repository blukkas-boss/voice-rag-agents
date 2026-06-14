"""PERF-004 — Milvus search latency smoke (requires live Milvus).

Marked `integration` (needs the Docker stack). Generous threshold: catches
pathological regressions, not micro latency. Skips if Milvus is unreachable.
"""

from __future__ import annotations

import os
import time
import uuid

import pytest

pytest.importorskip("pymilvus", reason="pymilvus not installed")

from voice_rag_agents.dataflows.interfaces import SearchRequest  # noqa: E402
from voice_rag_agents.dataflows.milvus_adapter import MilvusAdapter  # noqa: E402
from voice_rag_agents.dataflows.vector_records import VectorRecord  # noqa: E402

pytestmark = pytest.mark.integration

MILVUS_URI = os.environ.get("VOICE_RAG_MILVUS_URI", "http://localhost:19530")
DIM = 8
N = 1000
SEARCH_BUDGET_S = 3.0


@pytest.fixture(scope="module")
def loaded_collection():
    adapter = MilvusAdapter(uri=MILVUS_URI, timeout=15.0)
    if adapter.health().get("status") != "ok":
        pytest.skip(f"Milvus not reachable at {MILVUS_URI}")
    name = f"perf_{uuid.uuid4().hex[:8]}"
    adapter.ensure_collection(name, DIM)
    records = [
        VectorRecord(
            id=f"id-{i}",
            document_id=f"doc-{i}",
            chunk_id=f"chunk-{i}",
            chunk_text=f"record {i} about analytics and API limits",
            vector=[float((i + j) % 5 + 1) for j in range(DIM)],
            metadata={"i": i},
        )
        for i in range(N)
    ]
    adapter.upsert(name, records)
    yield adapter, name
    try:
        adapter._get_client().drop_collection(name)
    except Exception:  # noqa: BLE001
        pass


def test_perf004_milvus_search_latency(loaded_collection) -> None:
    adapter, name = loaded_collection
    query = [1.0] * DIM
    # warm up (load/index)
    adapter.search(name, SearchRequest(query_vector=query, top_k=5))
    start = time.perf_counter()
    out = adapter.search(name, SearchRequest(query_vector=query, top_k=5))
    elapsed = time.perf_counter() - start
    assert out, "expected search hits over 1000 records"
    assert elapsed < SEARCH_BUDGET_S, (
        f"Milvus search over {N} took {elapsed:.3f}s (budget {SEARCH_BUDGET_S}s)"
    )

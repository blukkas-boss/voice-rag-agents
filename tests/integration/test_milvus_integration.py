"""Integration tests against a live Milvus (IT-001..004).

Marked `integration`; run via `make integration-test` with the Docker stack up
(`make compose-up`). Each test skips cleanly if Milvus is unreachable, so the
suite never fails on a machine without the stack.

Milvus URI is taken from VOICE_RAG_MILVUS_URI (default http://localhost:19530).
"""

from __future__ import annotations

import os
import uuid

import pytest

pytest.importorskip("pymilvus", reason="pymilvus not installed")

from voice_rag_agents.dataflows.interfaces import SearchRequest  # noqa: E402
from voice_rag_agents.dataflows.milvus_adapter import MilvusAdapter  # noqa: E402
from voice_rag_agents.dataflows.vector_records import VectorRecord  # noqa: E402

pytestmark = pytest.mark.integration

MILVUS_URI = os.environ.get("VOICE_RAG_MILVUS_URI", "http://localhost:19530")
DIM = 8


@pytest.fixture(scope="module")
def adapter():
    a = MilvusAdapter(uri=MILVUS_URI, timeout=10.0)
    health = a.health()
    if health.get("status") != "ok":
        pytest.skip(f"Milvus not reachable at {MILVUS_URI}: {health.get('error')}")
    return a


@pytest.fixture(scope="module")
def collection(adapter):
    name = f"it_{uuid.uuid4().hex[:8]}"
    adapter.ensure_collection(name, DIM)
    yield name
    # Best-effort cleanup
    try:
        adapter._get_client().drop_collection(name)
    except Exception:  # noqa: BLE001
        pass


def _vec(seed: int) -> list[float]:
    return [float((seed + i) % 5 + 1) for i in range(DIM)]


def test_it001_milvus_health(adapter) -> None:
    health = adapter.health()
    assert health["status"] == "ok"
    assert "collections" in health


def test_it002_collection_creation(adapter, collection) -> None:
    client = adapter._get_client()
    assert collection in client.list_collections()
    # ensure_collection is idempotent
    adapter.ensure_collection(collection, DIM)
    assert collection in client.list_collections()


def test_it003_upsert_and_search(adapter, collection) -> None:
    records = [
        VectorRecord(
            id=f"id-{i}",
            document_id=f"doc-{i}",
            chunk_id=f"chunk-{i}",
            chunk_text=f"chunk text {i} about API rate limits",
            vector=_vec(i),
            metadata={"project": "Orion", "i": i},
        )
        for i in range(5)
    ]
    res = adapter.upsert(collection, records)
    assert res["upserted"] == 5

    out = adapter.search(collection, SearchRequest(query_vector=_vec(0), top_k=3))
    assert len(out) >= 1
    assert out[0].chunk_text
    assert out[0].document_id.startswith("doc-")


def test_it004_metadata_filter(adapter, collection) -> None:
    # Add a record from a different project, then filter by project.
    adapter.upsert(
        collection,
        [
            VectorRecord(
                id="id-apollo",
                document_id="doc-apollo",
                chunk_id="chunk-apollo",
                chunk_text="apollo project note",
                vector=_vec(9),
                metadata={"project": "Apollo"},
            )
        ],
    )
    out = adapter.search(
        collection,
        SearchRequest(query_vector=_vec(0), top_k=10, filters={"project": "Orion"}),
    )
    assert out, "expected at least one Orion result"
    assert all(r.metadata.get("project") == "Orion" for r in out), [
        r.metadata for r in out
    ]

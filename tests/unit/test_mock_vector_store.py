"""UT-017 / UT-018 / VRAG-B003: mock vector store upsert/search/filter."""
from __future__ import annotations


import pytest

from voice_rag_agents.dataflows.vector_records import (
    SearchRequest,
    VectorRecord,
)

pytestmark = pytest.mark.unit


def _unit_vector(dim: int, index: int) -> list[float]:
    """Return a unit vector with 1.0 at *index* and 0 elsewhere."""
    v = [0.0] * dim
    v[index % dim] = 1.0
    return v


# ---------------------------------------------------------------------------
# Upsert + search nearest-first (UT-017)
# ---------------------------------------------------------------------------


def test_mock_vector_upsert_search_nearest_first():
    """UT-017: search returns nearest record first."""
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    dim = 4
    records = [
        VectorRecord(
            id="far",
            document_id="doc-1",
            chunk_id="c1",
            chunk_text="far chunk",
            vector=_unit_vector(dim, 0),
            metadata={},
        ),
        VectorRecord(
            id="near",
            document_id="doc-1",
            chunk_id="c2",
            chunk_text="near chunk",
            vector=_unit_vector(dim, 1),
            metadata={},
        ),
    ]
    store.upsert("test_coll", records)

    # Query vector aligns with dimension 1 ("near")
    query = [0.0, 1.0, 0.0, 0.0]
    req = SearchRequest(query_vector=query, top_k=2)
    results = store.search("test_coll", req)

    assert len(results) == 2
    assert results[0].id == "near"
    assert results[0].score > results[1].score


def test_mock_vector_top_k_limit():
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    dim = 2
    records = [
        VectorRecord(
            id=f"r{i}",
            document_id="doc-1",
            chunk_id=f"c{i}",
            chunk_text=f"chunk {i}",
            vector=_unit_vector(dim, i % dim),
            metadata={},
        )
        for i in range(5)
    ]
    store.upsert("coll", records)
    req = SearchRequest(query_vector=[1.0, 0.0], top_k=3)
    results = store.search("coll", req)
    assert len(results) == 3


# ---------------------------------------------------------------------------
# Metadata filter (UT-018)
# ---------------------------------------------------------------------------


def test_mock_vector_metadata_filter():
    """UT-018: filter by metadata returns only matching records."""
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    dim = 2
    records = [
        VectorRecord(
            id="orion-1",
            document_id="doc-1",
            chunk_id="c1",
            chunk_text="Orion risk",
            vector=_unit_vector(dim, 0),
            metadata={"project": "Orion"},
        ),
        VectorRecord(
            id="apollo-1",
            document_id="doc-2",
            chunk_id="c2",
            chunk_text="Apollo risk",
            vector=_unit_vector(dim, 0),
            metadata={"project": "Apollo"},
        ),
        VectorRecord(
            id="orion-2",
            document_id="doc-1",
            chunk_id="c3",
            chunk_text="Orion decision",
            vector=_unit_vector(dim, 1),
            metadata={"project": "Orion"},
        ),
    ]
    store.upsert("coll", records)

    req = SearchRequest(
        query_vector=[1.0, 0.0],
        top_k=10,
        filters={"project": "Orion"},
    )
    results = store.search("coll", req)
    assert len(results) == 2
    assert all(r.metadata["project"] == "Orion" for r in results)


def test_mock_vector_filter_no_match():
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    store.upsert(
        "coll",
        [
            VectorRecord(
                id="r1",
                document_id="d1",
                chunk_id="c1",
                chunk_text="t",
                vector=[1.0, 0.0],
                metadata={"project": "Orion"},
            )
        ],
    )
    req = SearchRequest(
        query_vector=[1.0, 0.0], top_k=5, filters={"project": "NonExistent"}
    )
    results = store.search("coll", req)
    assert results == []


# ---------------------------------------------------------------------------
# Health + collection lifecycle
# ---------------------------------------------------------------------------


def test_mock_vector_health():
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    h = store.health()
    assert h["status"] == "ok"


def test_mock_vector_ensure_collection():
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    store.ensure_collection("new_coll", 2048)
    # Should not raise; upsert should work afterward
    store.upsert(
        "new_coll",
        [
            VectorRecord(
                id="r1",
                document_id="d1",
                chunk_id="c1",
                chunk_text="t",
                vector=[0.0],
                metadata={},
            )
        ],
    )


def test_mock_vector_delete_by_document_id():
    from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore

    store = MockVectorStore()
    store.upsert(
        "coll",
        [
            VectorRecord(
                id="r1",
                document_id="doc-1",
                chunk_id="c1",
                chunk_text="t1",
                vector=[1.0, 0.0],
                metadata={},
            ),
            VectorRecord(
                id="r2",
                document_id="doc-2",
                chunk_id="c2",
                chunk_text="t2",
                vector=[0.0, 1.0],
                metadata={},
            ),
        ],
    )
    result = store.delete_by_document_id("coll", "doc-1")
    assert result["deleted"] == 1
    req = SearchRequest(query_vector=[1.0, 0.0], top_k=10)
    remaining = store.search("coll", req)
    assert len(remaining) == 1
    assert remaining[0].document_id == "doc-2"

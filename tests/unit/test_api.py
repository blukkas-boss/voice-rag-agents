"""API tests — mock profile, no external services (uses TestClient)."""

from __future__ import annotations

import pytest

from voice_rag_agents.model_clients.provider_factory import reset_mock_vector_store


@pytest.fixture(autouse=True)
def _clean_store():
    reset_mock_vector_store()
    yield
    reset_mock_vector_store()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from voice_rag_agents.service.api import app

    return TestClient(app)


def test_health(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["profile"] == "mock"
    assert "providers" in body


def test_query_requires_input(client) -> None:
    resp = client.post("/query", json={})
    assert resp.status_code == 400


def test_ingest_then_query(client) -> None:
    ing = client.post(
        "/ingest",
        json={"documents": [{"text": "API rate limits may impact analytics.", "source_file": "m.md"}]},
    )
    assert ing.status_code == 200
    assert ing.json()["status"] == "success"

    q = client.post("/query", json={"question": "What are the API risks?"})
    assert q.status_code == 200
    body = q.json()
    assert body["answer"]
    assert len(body["citations"]) >= 1


def test_eval_run_stub(client) -> None:
    resp = client.post("/eval/run", json={})
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_implemented"

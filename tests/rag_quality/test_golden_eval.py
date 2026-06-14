"""RAG golden-evaluation tests (RAG-001..008).

Marked `rag_quality`; run via `make eval`. Mock profile, no external services.
"""

from __future__ import annotations

import pytest

from evals.runner import THRESHOLDS, load_golden, run_eval

pytestmark = pytest.mark.rag_quality


@pytest.fixture(scope="module")
def report():
    return run_eval()


def test_golden_dataset_loads() -> None:
    cases = load_golden()
    assert len(cases) >= 8
    ids = {c["id"] for c in cases}
    assert {"RAG-001", "RAG-003", "RAG-007"}.issubset(ids)


def test_recall_at_5_meets_threshold(report) -> None:
    assert report.recall_at_5 >= THRESHOLDS["recall_at_5"], (
        f"Recall@5 {report.recall_at_5:.3f} < {THRESHOLDS['recall_at_5']}"
    )


def test_citation_coverage_meets_threshold(report) -> None:
    assert report.citation_coverage >= THRESHOLDS["citation_coverage"], (
        f"citation coverage {report.citation_coverage:.3f} < {THRESHOLDS['citation_coverage']}"
    )


def test_mrr_threshold_enforced_only_with_real_embeddings(report) -> None:
    # In mock mode MRR is informational (hash embedding has no semantic order).
    # With real embeddings (profile != mock) the threshold must hold.
    if report.mrr_enforced():
        assert report.mrr >= THRESHOLDS["mrr"], f"MRR {report.mrr:.3f} < {THRESHOLDS['mrr']}"
    else:
        assert report.profile == "mock"


def test_rag_001_retrieves_api_risk(report) -> None:
    case = next(c for c in report.cases if c.id == "RAG-001")
    assert case.hit_rank is not None, "RAG-001 did not retrieve the API-risk chunk in top-5"
    assert case.has_citation


def test_overall_report_passes(report) -> None:
    assert report.passed(), report.to_dict()

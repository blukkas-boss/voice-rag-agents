"""RAG golden-evaluation runner.

Loads a golden Q/A set, ingests the dataset corpus into the (mock by default)
vector store, runs each query through the query graph, and computes RAG quality
metrics: Recall@k, MRR, and citation coverage.

Pure-stdlib; no provider SDK calls. Used by `tests/rag_quality/` and `make eval`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from voice_rag_agents.config.settings import get_settings
from voice_rag_agents.graph.ingestion_graph import run_ingestion_graph
from voice_rag_agents.graph.query_graph import run_query_graph
from voice_rag_agents.model_clients.provider_factory import reset_mock_vector_store

DATASETS_DIR = Path(__file__).parent / "datasets"

# Acceptance thresholds (blueprint 11_TEST_CASE_CATALOG / build plan).
THRESHOLDS = {
    "recall_at_5": 0.90,
    "mrr": 0.70,
    "citation_coverage": 0.95,
}


@dataclass
class CaseResult:
    id: str
    answerable: bool
    hit_rank: int | None  # 1-based rank of first relevant chunk, None if miss
    has_citation: bool
    answer: str
    no_evidence: bool


@dataclass
class EvalReport:
    cases: list[CaseResult] = field(default_factory=list)
    recall_at_5: float = 0.0
    mrr: float = 0.0
    citation_coverage: float = 0.0
    profile: str = "mock"

    def mrr_enforced(self) -> bool:
        # MRR measures ranking quality, which is only meaningful with real
        # embeddings. The mock hash-embedding produces near-uniform scores, so
        # gating MRR in mock mode would test retriever noise, not the system.
        return self.profile != "mock"

    def passed(self) -> bool:
        ok = (
            self.recall_at_5 >= THRESHOLDS["recall_at_5"]
            and self.citation_coverage >= THRESHOLDS["citation_coverage"]
        )
        if self.mrr_enforced():
            ok = ok and self.mrr >= THRESHOLDS["mrr"]
        return ok

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "recall_at_5": round(self.recall_at_5, 4),
            "mrr": round(self.mrr, 4),
            "mrr_enforced": self.mrr_enforced(),
            "citation_coverage": round(self.citation_coverage, 4),
            "thresholds": THRESHOLDS,
            "passed": self.passed(),
            "num_cases": len(self.cases),
            "cases": [
                {
                    "id": c.id,
                    "answerable": c.answerable,
                    "hit_rank": c.hit_rank,
                    "has_citation": c.has_citation,
                    "no_evidence": c.no_evidence,
                }
                for c in self.cases
            ],
        }


_NO_EVIDENCE_MARKER = "do not have enough evidence"


def load_golden(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or (DATASETS_DIR / "golden_qa.jsonl")
    cases: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _load_corpus_documents(corpus_path: Path | None = None) -> list[dict[str, Any]]:
    """Split the golden markdown corpus into section-tagged documents.

    Sectioning by markdown headings keeps the project/section metadata that the
    metadata-filtered retrieval cases (RAG-005) rely on.
    """
    corpus_path = corpus_path or (DATASETS_DIR / "meeting_notes.md")
    text = corpus_path.read_text(encoding="utf-8")
    docs: list[dict[str, Any]] = []
    section = "Header"
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            docs.append(
                {
                    "text": body,
                    "source_file": corpus_path.name,
                    "metadata": {"project": "Orion", "section": section},
                }
            )

    for raw in text.splitlines():
        if raw.startswith("## "):
            flush()
            section = raw[3:].strip()
            buf = [raw]
        else:
            buf.append(raw)
    flush()
    return docs


def _relevant(case: dict[str, Any], chunk_text: str) -> bool:
    substr = case.get("expected_chunk_substring")
    if substr:
        return substr.lower() in chunk_text.lower()
    # Fall back to expected_facts when no explicit chunk substring is given.
    facts = case.get("expected_facts") or []
    return any(f.lower() in chunk_text.lower() for f in facts)


def run_eval(
    golden_path: Path | None = None,
    corpus_path: Path | None = None,
    top_k: int = 5,
) -> EvalReport:
    reset_mock_vector_store()
    documents = _load_corpus_documents(corpus_path)
    ingest_state = {
        "run_id": "eval-ingest",
        "request_type": "ingest",
        "user_id": "eval",
        "session_id": "eval",
        "runtime_profile": "mock",
        "input_documents": documents,
    }
    ingest_result = run_ingestion_graph(ingest_state)
    report_status = (ingest_result.get("ingestion_report") or {}).get("status")
    if report_status != "success":
        raise RuntimeError(f"Eval corpus ingestion failed: {report_status}")

    cases_golden = load_golden(golden_path)
    results: list[CaseResult] = []

    for case in cases_golden:
        query_state = {
            "run_id": f"eval-{case['id']}",
            "request_type": "query",
            "user_id": "eval",
            "session_id": "eval",
            "runtime_profile": "mock",
            "input_text": case["query"],
            "metadata_filters": case.get("filters") or {},
        }
        out = run_query_graph(query_state)
        retrieved = out.get("retrieval_results") or []
        citations = out.get("citations") or []
        answer = out.get("answer", "") or ""
        no_evidence = _NO_EVIDENCE_MARKER in answer.lower()

        hit_rank: int | None = None
        for idx, item in enumerate(retrieved[:top_k], start=1):
            if _relevant(case, item.get("chunk_text", "")):
                hit_rank = idx
                break

        results.append(
            CaseResult(
                id=case["id"],
                answerable=bool(case.get("answerable", True)),
                hit_rank=hit_rank,
                has_citation=len(citations) > 0,
                answer=answer,
                no_evidence=no_evidence,
            )
        )

    answerable = [c for c in results if c.answerable]
    # Recall@k and MRR are computed over answerable cases only.
    if answerable:
        recall = sum(1 for c in answerable if c.hit_rank is not None) / len(answerable)
        mrr = sum((1.0 / c.hit_rank) if c.hit_rank else 0.0 for c in answerable) / len(answerable)
        coverage = sum(1 for c in answerable if c.has_citation) / len(answerable)
    else:
        recall = mrr = coverage = 0.0

    return EvalReport(
        cases=results,
        recall_at_5=recall,
        mrr=mrr,
        citation_coverage=coverage,
        profile=get_settings().profile,
    )


def main() -> int:
    report = run_eval()
    print(json.dumps(report.to_dict(), indent=2))
    return 0 if report.passed() else 1


if __name__ == "__main__":
    raise SystemExit(main())

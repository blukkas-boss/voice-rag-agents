# Build Plan — voice_rag_agents

Owner of this document: **exec/oversight shell** (acts as the Product
Orchestrator role from the blueprint). Build work is delegated to OpenClaw
sub-agents per wave; this shell sets up the environment, dispatches bounded
tasks, enforces gates, and reports — it does not hand-author product modules.

## Environment (verified Wave 0)

| Tool | Status |
|---|---|
| Python | 3.12.3 ✓ (spec needs 3.11+) |
| git | 2.43.0 ✓ (repo initialized) |
| Docker / Compose | **absent** — integration tests will be marked skipped per guardrails (doc 10) |
| Venv + editable install | ✓ `.venv`, `pip install -e ".[dev]"` |
| `make test` | ✓ 2 passed, no external services |

Safe assumptions applied (doc 10): proceed with mocks; real providers behind
interfaces; integration tests conditional on Docker.

## Delivery model — 5 waves (from 05_ORCHESTRATION_PLAN)

| Wave | Goal | Backlog tasks | Integration gate |
|---|---|---|---|
| 0 | Plan + scaffold | VRAG-A001/A002/A003 | `make test` passes, package imports, `.env.example` safe — **A001 DONE; A002/A003 pending** |
| 1 | Interfaces, schemas, mocks | VRAG-B001/B002/B003 | serialization + mock contract tests pass, no external services |
| 2 | Graph skeletons + node contracts | VRAG-C001..C005 | graph-path tests pass; QueryGraph cited mock answer; no-results → no-evidence |
| 3 | Real dataflow + provider adapters | VRAG-D001..D004, E001..E004, F001..F004, G001..G003 | unit + contract pass; mock graph tests still green; Milvus IT when Docker present |
| 4 | API, UI, deploy, security, docs | VRAG-H001/H002, I001..I003, J001..J003, K001..K003 | API mock tests, compose config validates, security tests pass |
| 5 | Testing workforce, hardening, acceptance | testing workforce + VRAG-L001/L002 | all P0 gates pass or blockers documented |

## Interface freeze (end of Wave 1)

`STTProvider`, `EmbeddingProvider`, `VectorStore`, `LLMProvider`, `Retriever`,
`PromptBuilder`, `CitationValidator`, `EvaluationScorer`. Changes after freeze
require impact note + backward-compat plan + updated tests.

## P0 acceptance (protect these)

mock-mode tests work · ingest sample notes · query sample notes · retrieve
correct chunk · cited answer · no-evidence fallback · basic API · core docs.

## Delegation log (oversight)

| Date | Wave/Task | Sub-agent | Result | Gate |
|---|---|---|---|---|
| 2026-06-13 | W0 VRAG-A001 scaffold | exec shell (direct) | repo, package, Makefile, .env.example, import+CLI test | `make test` ✓ 2 passed |
| 2026-06-13 | W1 interfaces/schemas/mocks | sub-agent | config, schemas, provider interfaces, deterministic mocks | tests ✓ |
| 2026-06-13 | W2 graph skeletons | sub-agent | 5 graphs, node contracts, checkpointer, conditional routing, run artifacts | 117 tests ✓ |
| 2026-06-14 | W3 real adapters | exec shell (direct; sub-agents hit rate-limit/idle-timeout/ctx-overflow) | doc loader, chunker, STT, embedding, LLM, Milvus, retrieval; graph nodes wired | 154 tests ✓, ruff ✓ |
| 2026-06-14 | W4 API/UI/deploy/security/docs | exec shell (direct) | FastAPI service, CLI subcommands, provider factory (profile-aware), Docker Compose+Dockerfile, healthcheck, security module, docs (install/operations/extension/openwebui); fixed Wave-2 graph double-wiring + undeclared-state-key drops so ingest→query works in mock mode | 164 tests ✓, ruff ✓, compose valid |
| 2026-06-14 | W5 testing workforce + VRAG-L001/L002 | exec shell (direct; sub-agents still daily-rate-limited) | golden dataset + eval runner (Recall@5/MRR/citation coverage, profile-aware MRR gate), tests/rag_quality + performance + regression suites, GT-005 no-evidence test, CI workflow, release_notes.md + acceptance_evidence.md + wave5_feedback_log.md | 177 tests ✓, ruff ✓, eval passed (R@5=1.0, cov=1.0) |

## Non-negotiable guardrails (doc 10) — enforced at review

1. No monolith. 2. No provider SDK calls inside graph nodes (interfaces only).
3. Unit tests never require external services. 4/5. No secrets committed/logged.
6. Retrieved text is untrusted data, never instructions. 7. No unsupported
answers on retrieval failure (no-evidence). 8. No skipping P0 tests. 9. No
swallowing failures in broad excepts. 10. Use documented safe assumptions
instead of asking.

## How modules are delivered (per blueprint)

Each module ships: interface · implementation · mock · unit tests · contract
tests · docs. Integration agent wires modules into the graph setup layer only.

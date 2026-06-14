# Release Notes — voice_rag_agents (Release Candidate)

Voice-to-answer Retrieval-Augmented Generation, local-first and modular, built on
LangGraph behind frozen provider interfaces. Runs fully in **mock mode** with no
external services; swaps to real providers (NVIDIA embeddings, Ollama LLM, Milvus)
via a single profile switch.

## What's in this release

- **Pipelines**: ingestion graph (load → chunk → embed → upsert) and query graph
  (transcribe → normalize → embed → retrieve → assemble → generate → validate
  citations/groundedness → format). Supervisor routing between them.
- **Providers behind frozen interfaces**: STT (command + HTTP), embeddings
  (OpenAI-compatible /v1/embeddings, e.g. NVIDIA), LLM (OpenAI-compatible
  /v1/chat/completions, e.g. Ollama), vector store (mock + Milvus REST adapter).
- **Provider factory**: profile-aware mock-vs-real selection; no provider SDK
  calls inside graph nodes.
- **Service surfaces**: FastAPI (`/ingest`, `/query`, `/eval/run`, `/health`) and
  a CLI (`voice-rag ingest|query|serve`).
- **Deploy**: Dockerfile + Docker Compose (API, Milvus, Ollama, Open WebUI),
  healthcheck script, `.env.example`.
- **Security**: path-traversal guard, secret redaction, prompt-injection
  detection/neutralization (retrieved text treated as untrusted data), file-type
  allowlist + size limits.
- **Quality**: golden RAG evaluation harness, performance smoke tests, regression
  tests, CI workflow.

## Setup

See `docs/INSTALL.md` (quick start in mock mode; real providers via Compose) and
`docs/OPERATIONS.md` (profiles, endpoints, troubleshooting).

```bash
make setup && make test          # mock mode, no services
make run-api                     # FastAPI on :8088
```

## Test evidence (mock profile, 2026-06-14)

| Gate | Command | Result |
|------|---------|--------|
| Unit + graph | `make test` | 176 passed, 1 skipped |
| Security | `make security-test` | 6 passed |
| RAG eval | `make eval` | 6 passed — Recall@5=1.0, citation coverage=1.0 |
| Performance smoke | `make performance-smoke` | 3 passed |
| Lint | `make lint` | ruff: all checks passed |
| Compose | `docker compose config` | valid YAML (Docker not installed here) |

The 1 skip is the Milvus adapter test (pymilvus/Docker absent).

## Known limitations / risks

- **Docker not available in this environment** → Milvus integration tests and
  the live Compose stack are skipped. The Compose config is validated and the
  adapter is unit-tested with `pymilvus` mocked. To run for real: install Docker,
  `make compose-up`, then `make integration-test`.
- **MRR threshold (≥0.70) is not enforced in mock mode.** The mock hash-embedding
  produces near-uniform similarity scores with no semantic ordering, so MRR over
  mock retrieval measures noise, not the system. Recall@5 (≥0.90) and citation
  coverage (≥0.95) are enforced in mock mode; MRR is enforced only when a real
  embedding provider is configured (`profile != mock`). See
  `docs/wave5_feedback_log.md` (W5-001).
- **Mock vector store is per-process.** CLI `ingest` then `query` are separate
  processes and do not share the in-memory store; use the API (single process) or
  a real Milvus backend for cross-call persistence.
- **No-evidence routing in mock mode**: the mock retriever always returns the
  corpus, so unanswerable golden cases still surface citations in mock mode. Real
  no-evidence behavior is exercised by graph test GT-005 (empty retrieval).

## Provenance

Built across 5 waves; see `docs/build_plan.md` delegation log. Waves 0, 3, 4, 5
built directly in the oversight session; waves 1–2 via sub-agents. Reason for
direct builds is recorded honestly in the log and `docs/wave5_feedback_log.md`
(free-tier model rate limits / local context limits during the build window).

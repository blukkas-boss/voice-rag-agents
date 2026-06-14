# Acceptance Evidence — voice_rag_agents

Run date: 2026-06-14 · Profile: `mock` · Commit: (see git log at tag rc)

This document captures the P0 acceptance gate (build plan) and the release
acceptance script (test catalog §"Release acceptance test script").

## P0 acceptance criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Mock-mode tests work | ✅ | `make test` → 176 passed, 1 skipped |
| 2 | Ingest sample notes | ✅ | API `POST /ingest` → `{"status":"success"}`; CLI `voice-rag ingest` |
| 3 | Query sample notes | ✅ | API `POST /query` → answer returned |
| 4 | Retrieve correct chunk | ✅ | RAG-001 retrieves the API-risk chunk in top-5 (Recall@5=1.0) |
| 5 | Cited answer | ✅ | `/query` returns `citations` (≥1) with label/chunk_id/source |
| 6 | No-evidence fallback | ✅ | Graph test GT-005 (empty retrieval) → no-evidence response |
| 7 | Basic API | ✅ | `/health`, `/ingest`, `/query`, `/eval/run` all respond |
| 8 | Core docs | ✅ | INSTALL, OPERATIONS, EXTENSION, openwebui_integration, release_notes |

## Release acceptance script

```
make test               -> 176 passed, 1 skipped
make security-test      -> 6 passed
make eval               -> 6 passed (Recall@5=1.0, MRR=0.497 [not enforced in mock], coverage=1.0)
make compose-up         -> SKIPPED (see below)
make integration-test   -> SKIPPED (see below)
make performance-smoke  -> 3 passed
make compose-down       -> SKIPPED (see below)
make lint               -> ruff: all checks passed
```

### Skipped integration dependency (recorded per catalog template)

```
Test skipped:   make compose-up / integration-test / compose-down; tests/unit/test_milvus_adapter.py
Reason:         Docker is not installed in this environment; pymilvus not installed.
Impact:         Milvus-backed integration paths (IT-001..004, PERF-004) and the
                live Compose stack are not exercised here. The Milvus adapter is
                unit-tested with pymilvus mocked; docker-compose.yml is validated
                as YAML; the API/graph paths are fully tested in mock mode.
How to run later: Install Docker, then:
                  cp .env.example .env   # set VOICE_RAG_PROFILE=local
                  make compose-up
                  docker compose exec ollama ollama pull llama3.1
                  make integration-test
                  make performance-smoke   # includes PERF-004 Milvus smoke
                  make compose-down
```

## RAG quality metrics (mock profile)

| Metric | Value | Threshold | Enforced (mock) | Verdict |
|--------|-------|-----------|-----------------|---------|
| Recall@5 | 1.000 | ≥ 0.90 | yes | ✅ |
| Citation coverage | 1.000 | ≥ 0.95 | yes | ✅ |
| MRR | 0.497 | ≥ 0.70 | no (mock embedding has no semantic order) | ⚠️ informational |

MRR is enforced only with a real embedding provider; rationale and the underlying
finding are logged in `docs/wave5_feedback_log.md` (W5-001). This is a documented
limitation of the mock embedding, not a system defect.

## Known limitations

See `docs/release_notes.md` → "Known limitations / risks". Summary: Docker/Milvus
not exercised in this environment; mock MRR informational; mock vector store is
per-process; mock no-evidence routing differs from real profiles.

## Verdict

All P0 criteria pass in mock mode. The only un-exercised gates are Docker/Milvus
integration, which are environment-blocked and documented with exact run-later
steps. **Release candidate accepted with documented limitations.**

# Operations

## Profiles

`VOICE_RAG_PROFILE` selects the provider set:

| Profile        | STT/Embedding/LLM/Vector store | External services |
|----------------|--------------------------------|-------------------|
| `mock`         | Deterministic mocks            | None (default)    |
| `local`        | Real adapters via Docker stack | Milvus, Ollama    |
| `integration`  | Real adapters + integration tests | Docker          |

The provider factory (`model_clients/provider_factory.py`) is the single place
that maps profile → provider. Graph nodes never instantiate providers directly.

## Running

- API: `make run-api` or `voice-rag serve --port 8088`
- CLI: `voice-rag ingest <path>`, `voice-rag query "<question>"`
- Stack: `make compose-up` / `make compose-down`
- Health: `make health` (or `bash scripts/healthcheck.sh`)

## Endpoints

- `GET  /health` — service + provider summary
- `POST /ingest` — `{documents:[{text, source_file}], path?}`
- `POST /query`  — `{question?, audio_path?, top_k?, filters?}`
- `POST /eval/run` — golden eval batch (runner lands in Wave 5)

## Observability

Each graph run can emit a JSONL artifact via
`observability/run_artifacts.py` (run id, node timings, provider, retrieval
top-k ids/scores, citations, warnings/errors, final status). Artifacts go to
`VOICE_RAG_ARTIFACT_DIR` (default `./artifacts`).

## Quality gates (`make` targets)

```
make test               # unit + graph (no services)
make security-test      # path traversal, secret redaction, injection
make integration-test   # Milvus-backed (Docker required)
make eval               # RAG golden eval (Wave 5)
make performance-smoke  # latency smoke (Wave 5)
make lint               # ruff
```

## Troubleshooting

- **`/query` returns no-evidence after CLI ingest** — mock store is per-process;
  use the API or a real Milvus backend.
- **Milvus tests skipped** — expected without Docker; they are service-gated.
- **500 from API in a real profile** — check provider URLs/keys in `.env`;
  `/health` shows the configured providers.

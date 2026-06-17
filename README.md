# voice_rag_agents

Modular, LangGraph-orchestrated, **local-first voice-to-answer RAG**.
Speech or text in → a grounded, **cited** answer out — with an automated
RAG/security/performance evaluation suite built in.

It runs fully in a **mock profile with no external services**, then swaps to
real providers (NVIDIA embeddings, Ollama LLM, Milvus vector store) via a single
profile switch. All providers sit behind frozen interfaces, so no provider SDK
calls leak into the orchestration graph.

- **License:** MIT
- **Python:** 3.11+
- **Tested:** 164 unit/graph tests, runnable with zero external services

## What it does

1. Accept voice or text.
2. Local STT (Whisper.cpp / compatible) for voice input.
3. Embed query + documents (NVIDIA Llama Nemotron Embed VL, or a mock provider).
4. Store and search vectors + metadata in Milvus.
5. Generate a grounded, **cited** answer with a local LLM (Ollama / any
   OpenAI-compatible endpoint).
6. Validate every answer for citation correctness and groundedness.
7. Expose via FastAPI + an Open WebUI integration.

## Install

Requirements: Python 3.11+ (and Docker + Docker Compose only if you want the
real provider stack).

```bash
git clone https://github.com/blukkas-boss/voice-rag-agents.git
cd voice-rag-agents
make setup          # create .venv and install (editable) with dev extras
make test           # 164 tests, no external services required
cp .env.example .env
```

### Try it via CLI (mock mode)

```bash
mkdir -p data/input
echo "API rate limits may impact analytics." > data/input/notes.md
voice-rag ingest data/input/notes.md
voice-rag query "What are the API risks?"
```

> In mock mode the vector store is in-memory and **per-process**. CLI `ingest`
> and `query` are separate processes, so use the API (single process) or a real
> Milvus backend to share state across ingest and query.

### Try it via API (mock mode)

```bash
make run-api                      # uvicorn on :8088
curl localhost:8088/health
curl -X POST localhost:8088/ingest -H 'content-type: application/json' \
  -d '{"documents":[{"text":"API rate limits may impact analytics.","source_file":"m.md"}]}'
curl -X POST localhost:8088/query -H 'content-type: application/json' \
  -d '{"question":"What are the API risks?"}'
```

### Run with real providers (local stack)

```bash
cp .env.example .env              # set VOICE_RAG_PROFILE=local
# configure embedding base URL/key, Ollama URL, and Milvus URI in .env
make compose-up                   # Milvus + Ollama + Open WebUI + API
docker compose exec ollama ollama pull llama3.1
make integration-test             # Milvus-backed tests (only when stack is up)
```

Full instructions: **[docs/INSTALL.md](docs/INSTALL.md)**.

## Runtime profiles

| Profile | Services |
|---|---|
| `mock` | none (unit + graph tests) |
| `local` | Milvus, Ollama, local STT |
| `integration` | Docker-backed services |
| `production-local` | full local stack + Open WebUI |

## Architecture

Explicit LangGraph orchestration — a supervisor routes between `Ingestion`,
`Query`, `Admin`, and `Evaluation` subgraphs. All providers live behind
interfaces and a profile-aware factory selects mock vs. real implementations.

Ingestion graph: `load → chunk → embed → upsert`.
Query graph: `transcribe → normalize → embed → retrieve → assemble → generate →
validate citations/groundedness → format`.

## Repo map

- `src/voice_rag_agents/` — the package (agents, dataflows, graph, model_clients, service, …)
- `tests/` — unit, graph, integration, rag_quality, security, performance
- `evals/` — golden datasets + runner
- `docs/` — install, operations, extension, and Open WebUI integration guides

## Documentation

- [docs/INSTALL.md](docs/INSTALL.md) — installation and first run
- [docs/OPERATIONS.md](docs/OPERATIONS.md) — running, endpoints, evals
- [docs/EXTENSION.md](docs/EXTENSION.md) — add a new provider behind the interfaces
- [docs/openwebui_integration.md](docs/openwebui_integration.md) — Open WebUI setup
- [docs/release_notes.md](docs/release_notes.md) — what's in this release

## License

MIT — see [LICENSE](LICENSE).

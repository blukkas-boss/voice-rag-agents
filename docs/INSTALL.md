# Installation

voice_rag_agents is local-first. It runs in **mock mode** with zero external
services, and switches to real providers (NVIDIA embeddings, Ollama LLM, Milvus
vector store) when you configure a non-mock profile.

## Requirements

- Python 3.11+
- (Optional, for real integrations) Docker + Docker Compose

## Quick start (mock mode, no services)

```bash
make setup          # create .venv and install with dev extras
make test           # 164 tests, no external services
cp .env.example .env
```

### Try it via CLI

```bash
mkdir -p data/input
echo "API rate limits may impact analytics." > data/input/notes.md
voice-rag ingest data/input/notes.md
voice-rag query "What are the API risks?"
```

> Note: in mock mode the vector store is in-memory and **per-process**. CLI
> `ingest` and `query` are separate processes, so use the API (single process)
> or a real Milvus backend to share state across ingest/query.

### Try it via API

```bash
make run-api                      # uvicorn on :8088 (mock profile)
curl localhost:8088/health
curl -X POST localhost:8088/ingest -H 'content-type: application/json' \
  -d '{"documents":[{"text":"API rate limits may impact analytics.","source_file":"m.md"}]}'
curl -X POST localhost:8088/query -H 'content-type: application/json' \
  -d '{"question":"What are the API risks?"}'
```

## Real providers (local integration)

1. Install Docker and ensure it is running.
2. `cp .env.example .env` and set `VOICE_RAG_PROFILE=local` (or `integration`).
3. Configure provider settings in `.env` (embedding base URL/key, Ollama URL, Milvus URI).
4. `make compose-up` — starts Milvus, Ollama, Open WebUI, and the API.
5. Pull an Ollama model: `docker compose exec ollama ollama pull llama3.1`
6. `make integration-test` (runs Milvus-backed tests when the stack is up).

Tests never require real services; they are gated by the `integration`/`external`
pytest markers and skipped by default.

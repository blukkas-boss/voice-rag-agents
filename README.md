# voice_rag_agents

Modular, LangGraph-orchestrated, **local-first voice-to-answer RAG** product.
Speech or text in → grounded, **cited** answer out, with an independent
automated testing workforce.

> Status: **Wave 0 — scaffold.** The package skeleton, tooling, and build plan
> exist; provider adapters and graphs are implemented by the build workforce in
> later waves. See `docs/build_plan.md` and `docs/blueprint/`.

## Quickstart (dev)

```bash
make setup     # create .venv and install (editable) with dev extras
make test      # run unit + graph tests — no external services required
```

## What it does (target)

1. Accept voice or text.
2. Local STT (Whisper.cpp / Cipher / compatible) for voice.
3. Embed query + documents (NVIDIA Llama Nemotron Embed VL 1B V2, mockable).
4. Store/search vectors + metadata in Milvus.
5. Generate a grounded, cited answer with a local LLM (Ollama / OpenAI-compatible).
6. Expose via FastAPI + Open WebUI integration.
7. Continuously validate with automated RAG/security/perf evals.

## Architecture

Explicit LangGraph orchestration (`SupervisorGraph` → `Ingestion` / `Query` /
`Admin` / `Evaluation` subgraphs), all providers behind interfaces, runnable in
a `mock` profile with **no external services**. See
`docs/blueprint/02_LANGGRAPH_PRODUCT_ARCHITECTURE.md`.

## Runtime profiles

| Profile | Services |
|---|---|
| `mock` | none (unit + graph tests) |
| `local` | Milvus, Ollama, local STT |
| `integration` | Docker-backed services |
| `production-local` | full local stack + Open WebUI |

## Repo map

- `src/voice_rag_agents/` — the package (agents, dataflows, graph, model_clients, service, …)
- `tests/` — unit, graph, integration, rag_quality, security, performance
- `evals/` — golden datasets + runners
- `docs/blueprint/` — the source specification bundle
- `docs/build_plan.md` — orchestration plan + backlog mapping

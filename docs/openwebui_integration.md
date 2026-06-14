# Open WebUI Integration

Open WebUI is the user-facing chat interface. It connects to Ollama for model
serving, and to the `voice_rag_agents` API for grounded, cited answers.

The product is fully testable **without** Open WebUI running.

## Architecture

```
Open WebUI chat
   -> tool/pipeline
   -> voice_rag_agents FastAPI (/query)
   -> LangGraph QueryGraph
   -> answer with citations
```

## Setup

1. Start the stack: `make compose-up`
   - Open WebUI: http://localhost:3000
   - voice_rag_agents API: http://localhost:8088
   - Ollama: http://localhost:11434
2. Pull a model: `docker compose exec ollama ollama pull llama3.1`
3. Open http://localhost:3000 and create an account (first user is admin).

## Connect Open WebUI to the RAG API (Pipelines / Tools)

Open WebUI calls the RAG API as an external tool. Configure a custom tool /
pipeline that POSTs to the query endpoint:

```
POST http://voice-rag-api:8088/query
Content-Type: application/json

{ "question": "<user message>" }
```

Response:

```json
{
  "run_id": "run-...",
  "answer": "… [S1]",
  "citations": [{"label": "S1", "chunk_id": "...", "source_file": "..."}],
  "final_status": "success"
}
```

Render `answer` in the chat, and optionally list `citations` as sources.

## Ingesting documents

Use the API or CLI before querying:

```bash
curl -X POST http://localhost:8088/ingest -H 'content-type: application/json' \
  -d '{"path": "/data/input"}'
```

## Configuration vs customization

- **Configuration**: model selection, base URLs, and the RAG tool endpoint are
  set via environment / Open WebUI settings — no code changes.
- **Customization**: changing prompt formatting, citation rendering, or adding a
  reranker is a code change in `voice_rag_agents` (see `docs/EXTENSION.md`),
  behind the frozen interfaces.

## Without Open WebUI

Everything works via `make run-api` + curl, or the `voice-rag` CLI. Open WebUI
is an optional presentation layer.

# LangGraph Product Architecture

## Architecture intent

This project should not be a simple wrapper around Open WebUI, Milvus, and Ollama. It should be a modular product with an explicit LangGraph orchestration layer that can be used from a UI, CLI, API, scheduled ingestion job, or automated evaluation runner.

The design should mirror the modular decomposition pattern of a multi-agent system:

- Agents are specialized roles.
- Dataflows handle data movement and provider interaction.
- Graphs define stateful orchestration, routing, retries, debates, quality gates, and completion.
- Clients isolate LLM, embedding, STT, and vector database providers.
- Config provides environment-driven runtime profiles.

## Target logical architecture

```text
User / Open WebUI / API Client
        |
        v
FastAPI Orchestration Service
        |
        v
SupervisorGraph
   |------------------|----------------|----------------|
   v                  v                v                v
IngestionGraph     QueryGraph       AdminGraph       EvaluationGraph
   |                  |                |                |
   v                  v                v                v
Dataflows        STT/Embedding     Health/Reindex   Test/Eval runners
Parsers          Milvus Search     Backup/Migrate   Metrics/Reports
Chunkers         Context Builder
Embedding        Local LLM
Milvus Upsert    Citation Validator
```

## Repository layout

```text
voice_rag_agents/
  README.md
  pyproject.toml
  .env.example
  docker-compose.yml
  Makefile
  src/voice_rag_agents/
    __init__.py
    default_config.py
    agents/
      __init__.py
      ingestion/
      query/
      retrieval/
      answer/
      admin/
      evaluation/
      utils/
      schemas.py
    config/
      __init__.py
      settings.py
      profiles.py
      env.py
    dataflows/
      __init__.py
      loaders.py
      parsers.py
      chunking.py
      metadata.py
      vector_records.py
      milvus_store.py
      ingestion_pipeline.py
    graph/
      __init__.py
      states.py
      setup.py
      supervisor_graph.py
      ingestion_graph.py
      query_graph.py
      admin_graph.py
      evaluation_graph.py
      conditional_logic.py
      checkpointer.py
      propagation.py
      quality_gates.py
    model_clients/
      __init__.py
      stt_client.py
      embedding_client.py
      llm_client.py
      ollama_client.py
      nvidia_embedding_client.py
      mock_clients.py
    service/
      __init__.py
      api.py
      schemas.py
      dependencies.py
    ui_integrations/
      __init__.py
      openwebui_tools.py
      openwebui_pipeline.md
    observability/
      __init__.py
      logging.py
      tracing.py
      run_artifacts.py
    utils/
      tokens.py
      files.py
      ids.py
      errors.py
  tests/
  evals/
  docs/
```

## Graphs

### SupervisorGraph

Purpose: route a request to the correct subgraph.

Inputs:

- User request.
- Request type if known: `ingest`, `query`, `admin`, `eval`.
- Runtime profile.

Outputs:

- Final response.
- Graph run summary.
- Errors or human action requirements.

Routes:

```text
START -> classify_request -> route
route -> IngestionGraph if documents are provided or command is ingest
route -> QueryGraph if user asks a question
route -> AdminGraph if command is health, reindex, backup, migrate
route -> EvaluationGraph if command is eval
subgraph -> summarize_run -> END
```

### IngestionGraph

Purpose: turn source documents into stored vector records.

Nodes:

1. `discover_sources`
2. `load_documents`
3. `parse_documents`
4. `normalize_documents`
5. `chunk_documents`
6. `extract_metadata`
7. `embed_chunks`
8. `validate_embeddings`
9. `prepare_vector_records`
10. `ensure_collection`
11. `upsert_records`
12. `verify_ingestion`
13. `write_ingestion_report`

Key conditional routes:

- If a file type is unsupported, skip safely and log.
- If parsing fails, route to `quarantine_document`.
- If embedding provider fails, retry, then fallback to mock only in test mode.
- If Milvus unavailable, fail with actionable diagnostic.
- If duplicate document hash exists, either skip or reindex based on config.

### QueryGraph

Purpose: turn a user question into a grounded answer.

Nodes:

1. `accept_query`
2. `transcribe_voice` if voice input exists.
3. `normalize_query`
4. `rewrite_query` optional.
5. `embed_query`
6. `search_vector_store`
7. `metadata_filter_results`
8. `rerank_results` optional.
9. `assemble_context`
10. `generate_answer`
11. `validate_citations`
12. `validate_groundedness`
13. `format_response`

Key conditional routes:

- If STT confidence is low, ask for clarification or return transcript confirmation.
- If no retrieval results, return no-evidence response.
- If retrieved context has prompt injection, sanitize and flag.
- If generated answer lacks citations, regenerate once with stricter prompt.
- If still ungrounded, return safe no-evidence answer with sources only.

### AdminGraph

Purpose: operate the product.

Nodes:

- `health_check_services`
- `validate_config`
- `validate_embedding_dim`
- `ensure_schema`
- `backup_collection`
- `restore_collection`
- `reindex_collection`
- `purge_collection`
- `write_admin_report`

### EvaluationGraph

Purpose: run ongoing validation.

Nodes:

- `load_eval_dataset`
- `run_ingestion_fixture`
- `run_retrieval_tests`
- `run_answer_tests`
- `run_security_tests`
- `run_performance_tests`
- `score_results`
- `write_eval_report`
- `raise_quality_gate_status`

## Core state model

Implement a typed state object using `TypedDict` or Pydantic models.

```python
class VoiceRAGState(TypedDict, total=False):
    run_id: str
    request_type: Literal['ingest', 'query', 'admin', 'eval']
    user_id: str
    session_id: str
    created_at: str
    runtime_profile: str

    # inputs
    input_text: str | None
    input_audio_path: str | None
    input_documents: list[dict]
    command: str | None

    # speech
    transcript: str | None
    stt_confidence: float | None

    # ingestion
    documents: list[DocumentRecord]
    chunks: list[ChunkRecord]
    embeddings: list[EmbeddingRecord]
    vector_records: list[VectorRecord]
    ingestion_report: dict

    # query
    normalized_query: str
    rewritten_query: str | None
    query_embedding: list[float]
    retrieval_results: list[RetrievalResult]
    assembled_context: str

    # answer
    answer: str
    citations: list[Citation]
    answer_quality: dict

    # control
    errors: list[GraphError]
    warnings: list[str]
    retries: dict[str, int]
    human_actions_required: list[str]
    final_status: Literal['success', 'partial', 'failed']
```

## Package-level modules and contracts

| Module | Responsibility |
|---|---|
| `agents/` | Agent node factories and role-specific logic. |
| `dataflows/` | Pure data movement, parsing, chunking, metadata, vector record creation. |
| `graph/` | LangGraph state, graph setup, conditional routes, subgraph assembly. |
| `model_clients/` | Provider adapters for STT, embedding, LLM, and mocks. |
| `service/` | FastAPI endpoints for ingestion, query, health, eval. |
| `ui_integrations/` | Open WebUI tool/pipeline integration instructions and code. |
| `observability/` | Logs, traces, run artifacts, timings. |
| `tests/` | Unit, graph, integration, security, RAG quality, performance tests. |
| `evals/` | Golden datasets and evaluation reports. |

## Product assembly model

Each subagent produces a module with:

1. Interface.
2. Implementation.
3. Mock implementation.
4. Unit tests.
5. Contract tests.
6. Documentation.

The Integration Agent assembles modules by wiring them into the graph setup layer. No module should call another provider directly unless it goes through the approved interface.

## Runtime modes

| Mode | Purpose | External services |
|---|---|---|
| `mock` | Unit and graph tests. | None. |
| `local` | Developer demo. | Milvus, Ollama, local STT, optional embedding endpoint. |
| `integration` | Docker-backed tests. | Milvus, API, optionally Ollama. |
| `production-local` | Hardened local deployment. | Milvus, Open WebUI, Ollama, STT, embedding endpoint. |

## Configuration principles

- All provider choices are config-driven.
- Environment variables override defaults.
- `.env.example` must contain all keys with safe defaults.
- Secrets must never be committed.
- Tests must not require secrets.
- Model dimensions must be validated before collection creation.

## Minimum API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check. |
| `/ingest` | POST | Ingest documents. |
| `/query` | POST | Run text or voice query. |
| `/collections` | GET | List vector collections. |
| `/admin/reindex` | POST | Reindex documents. |
| `/eval/run` | POST | Run evaluation suite. |
| `/metrics` | GET | Runtime metrics if enabled. |

## Required quality gates in graph

1. Embedding dimension matches collection schema.
2. Retrieved chunks include source metadata.
3. Answer citations map to retrieved chunks.
4. Answer does not claim unsupported facts.
5. Runtime errors are captured in state.
6. Unsafe documents and prompts are sanitized before LLM prompt assembly.
7. Low confidence STT does not silently produce a confident answer.

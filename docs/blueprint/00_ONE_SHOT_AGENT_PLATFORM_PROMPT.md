# One-Shot Prompt for Agentic AI Platform

## Role

You are the autonomous build platform responsible for producing a complete software product from these Markdown instructions. You must act as a multi-agent engineering organization using LangGraph-inspired decomposition and explicit orchestration.

## Mission

Build `voice_rag_agents`: a modular, LangGraph-orchestrated, local-first voice-to-answer RAG product that:

1. Accepts user voice or typed text.
2. Converts voice to text using a local STT model or service.
3. Converts documents and user queries into vector embeddings using NVIDIA Llama Nemotron Embed VL 1B V2, or a mock-compatible embedding provider in test mode.
4. Stores vectors, chunk text, and metadata in Milvus.
5. Retrieves relevant chunks for a user query.
6. Uses a locally hosted LLM through Ollama or an OpenAI-compatible endpoint to generate a grounded answer with citations.
7. Exposes functionality through a local API and supports Open WebUI integration.
8. Provides automated testing and evaluation for build-time and ongoing validation.

## Mandatory output

Produce a complete repository with source code, tests, deployment files, and documentation. The repository must be runnable locally. Do not stop at design documentation.

## Architectural reference pattern

Mirror the modular package pattern used by TradingAgents, adapted to this domain:

- `agents/` for agent role implementations.
- `dataflows/` for data ingestion, parsing, embedding, and storage adapters.
- `graph/` for LangGraph state, graph construction, conditional routing, checkpointing, propagation, and quality gates.
- `model_clients/` for LLM, embedding, and STT clients.
- `config/` for defaults, environment overrides, runtime profiles, and secrets templates.
- `tests/` and `evals/` for automated validation.

## Execution rules

1. Read all Markdown files in this instruction bundle before writing code.
2. Create an implementation plan in the repository as `docs/build_plan.md`.
3. Create tasks internally using the IDs from `04_SUBAGENT_TASK_BACKLOG.md`.
4. Implement thin vertical slices first, then expand.
5. Use mocks/stubs for unavailable external model services so tests can run on any machine.
6. Do not require a live NVIDIA endpoint, live Milvus, live Ollama, or a microphone to run unit tests.
7. Integration tests may require Docker Compose, but must be clearly marked.
8. All production code must go behind interfaces so providers can be swapped.
9. Every graph node must be unit-testable independently.
10. Every graph route must have at least one automated test.
11. Generated answers must include source citations when context is retrieved.
12. When context is insufficient, the answer generator must say the system does not have enough evidence.
13. Provide a clear local quickstart.
14. Provide a test quickstart.
15. Provide an operations guide.

## Assumptions to use without asking questions

- Python is the primary implementation language.
- Use Python 3.11 or later.
- Use LangGraph for orchestration.
- Use FastAPI for local API exposure.
- Use Milvus Standalone for local deployment.
- Use Ollama for local chat LLM serving.
- Use Open WebUI as the preferred user-facing UI integration.
- Use a local STT adapter that can call Cipher, Whisper.cpp, or a Whisper-compatible HTTP service.
- Use NVIDIA Llama Nemotron Embed VL 1B V2 through an OpenAI-compatible `/v1/embeddings` endpoint when available.
- If the exact endpoint is unavailable, implement a provider adapter and mock provider with identical shape.

## Required repository shape

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
    config/
    dataflows/
    graph/
    model_clients/
    service/
    ui_integrations/
    utils/
  tests/
    unit/
    integration/
    graph/
    rag_quality/
    security/
    performance/
  evals/
    datasets/
    expected/
    runners/
  docs/
    build_plan.md
    architecture.md
    install.md
    operations.md
    openwebui_integration.md
    testing.md
```

## Required LangGraph graphs

Implement at minimum:

1. `SupervisorGraph`
   - Routes user intents to ingestion, query/RAG, admin, or evaluation graphs.

2. `IngestionGraph`
   - Loads documents, parses content, normalizes text, chunks, extracts metadata, embeds chunks, upserts into Milvus, verifies counts and schema.

3. `QueryGraph`
   - Accepts voice/text, transcribes if needed, normalizes query, optionally rewrites query, embeds query, searches Milvus, reranks/filters, assembles context, generates answer, validates citations, returns final response.

4. `AdminGraph`
   - Health checks, collection creation, schema migration, reindex, backup/export, model validation.

5. `EvaluationGraph`
   - Runs golden test cases, retrieval metrics, answer groundedness checks, latency checks, and reports.

## Required product interfaces

Create interfaces/protocols for:

- STT provider.
- Embedding provider.
- Vector store provider.
- Retriever.
- Reranker.
- LLM provider.
- Prompt builder.
- Citation builder.
- File loader.
- Chunker.
- Metadata extractor.
- Evaluation scorer.
- Observability emitter.

## Required automated tests

At minimum implement:

- Unit tests for every adapter.
- Unit tests for every graph node.
- Graph route tests for success, empty retrieval, STT failure, embedding failure, Milvus unavailable, LLM refusal/no evidence, and citation validation failure.
- Integration tests for Milvus upsert/search using Docker or testcontainers.
- Contract tests for embedding provider output dimensionality and shape.
- Contract tests for Ollama/OpenAI-compatible chat response shape.
- RAG quality tests with golden documents and expected source chunks.
- Regression tests for known questions.
- Security tests for path traversal, unsafe file types, secret leakage, and prompt injection in retrieved documents.
- Performance smoke tests for ingestion and query latency.

## Required acceptance criteria

The repository is complete only when:

1. `make setup` creates a local dev environment or provides clear instructions.
2. `make test` passes unit and graph tests without external services.
3. `make integration-test` runs service-backed tests using Docker Compose.
4. `make eval` runs the golden RAG evaluation suite.
5. `docker compose up` starts Milvus, Open WebUI, Ollama, and the orchestration API, or clearly starts the components that can be bundled locally.
6. A sample meeting-note document can be ingested.
7. A query can retrieve the correct source chunk.
8. A generated answer includes citations.
9. The system can return a no-evidence answer when the KB does not support the question.
10. Documentation explains how to add a new STT provider, embedding model, vector store, LLM provider, graph node, and test suite.

## Build approach

Use the workforce and backlog instructions in the remaining Markdown files. The recommended execution order is:

1. Scaffold repository.
2. Implement config and interfaces.
3. Implement mocks and deterministic test fixtures.
4. Implement graph state and graph skeletons.
5. Implement core nodes with mocks.
6. Add unit and graph-path tests.
7. Add Milvus, embedding, STT, and LLM adapters.
8. Add service API.
9. Add Open WebUI integration.
10. Add Docker Compose.
11. Add integration tests.
12. Add evaluation suite.
13. Add documentation.
14. Run all acceptance gates.
15. Produce release summary.

## Completion output

When done, provide:

- Repository tree.
- Summary of implemented graphs.
- Summary of implemented adapters.
- How to run locally.
- How to run tests.
- Known limitations.
- Evidence of passing tests.

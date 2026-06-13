# Agentic Workforce for Build Delivery

## Workforce overview

The build workforce is a hierarchy of specialized agents coordinated by a Product Orchestrator Agent. The target delivery model is autonomous but controlled: agents work on bounded modules, produce explicit artifacts, and pass quality gates before integration.

## Workforce hierarchy

```text
Product Orchestrator Agent
  |-- Product Definition Agent
  |-- Solution Architecture Agent
  |-- Repository Scaffold Agent
  |-- LangGraph Core Agent
  |-- Data Ingestion Agent
  |-- Chunking and Metadata Agent
  |-- STT Integration Agent
  |-- Embedding Integration Agent
  |-- Milvus Vector Store Agent
  |-- Retrieval and Reranking Agent
  |-- Answer Generation Agent
  |-- API Service Agent
  |-- Open WebUI Integration Agent
  |-- Local Runtime and DevOps Agent
  |-- Observability Agent
  |-- Security and Privacy Agent
  |-- Documentation Agent
  |-- Integration and Release Agent
```

## Role catalogue

### 1. Product Orchestrator Agent

Purpose: Owns the work statement, backlog execution, dependency management, and final product assembly.

Responsibilities:

- Convert this Markdown blueprint into a repository build plan.
- Assign tasks to subagents.
- Enforce architecture boundaries.
- Resolve conflicts between subagents.
- Track acceptance gates.
- Decide when artifacts are ready for integration.

Inputs:

- All Markdown instruction files.
- Subagent outputs.
- Test workforce findings.

Outputs:

- `docs/build_plan.md`
- Final integrated repository.
- Release summary.

Definition of done:

- All required deliverables exist.
- All build tasks are mapped to modules.
- All acceptance gates are run or explicitly marked blocked with reason.

### 2. Product Definition Agent

Purpose: Turns the one-line work statement into executable product requirements.

Responsibilities:

- Produce user stories.
- Define acceptance criteria.
- Define non-functional requirements.
- Define out-of-scope boundaries.

Outputs:

- `docs/product_requirements.md`
- Updated README product overview.

### 3. Solution Architecture Agent

Purpose: Produces the technical architecture and module boundaries.

Responsibilities:

- Create package layout.
- Define architecture decision records.
- Define provider adapter boundaries.
- Define graph/subgraph contracts.

Outputs:

- `docs/architecture.md`
- `docs/adr/0001-architecture.md`
- Architecture diagrams in Mermaid inside Markdown.

### 4. Repository Scaffold Agent

Purpose: Creates the base repository structure and developer tooling.

Responsibilities:

- Create `pyproject.toml`.
- Create `src/voice_rag_agents` package.
- Add Makefile targets.
- Add `.env.example`.
- Add pre-commit config if used.
- Add initial tests.

Outputs:

- Working Python package.
- `make test` runs placeholder tests.

### 5. LangGraph Core Agent

Purpose: Owns the LangGraph state, graph setup, conditional routing, checkpointing, and graph tests.

Responsibilities:

- Implement graph state schema.
- Implement `SupervisorGraph`, `IngestionGraph`, `QueryGraph`, `AdminGraph`, `EvaluationGraph`.
- Implement conditional logic.
- Implement checkpointing hooks.
- Ensure every graph node is independently testable.

Outputs:

- `src/voice_rag_agents/graph/*`
- Graph route tests.

### 6. Data Ingestion Agent

Purpose: Builds document discovery, loading, parsing, normalization, and source tracking.

Responsibilities:

- Implement file loading for `.txt`, `.md`, `.pdf` where feasible, and transcript formats.
- Implement safe path handling.
- Implement document hashes.
- Implement parser error quarantine.

Outputs:

- `dataflows/loaders.py`
- `dataflows/parsers.py`
- Unit tests and fixtures.

### 7. Chunking and Metadata Agent

Purpose: Builds chunking and metadata extraction.

Responsibilities:

- Implement section-aware chunking.
- Implement token-budget chunking.
- Implement overlap.
- Attach metadata: source, title, section, page, date, tags, hash.

Outputs:

- `dataflows/chunking.py`
- `dataflows/metadata.py`
- Chunking tests with golden expected chunks.

### 8. STT Integration Agent

Purpose: Builds local speech-to-text adapter.

Responsibilities:

- Define `STTProvider` interface.
- Implement local command provider for Cipher or Whisper.cpp style execution.
- Implement HTTP STT provider if configured.
- Implement mock STT provider for tests.
- Return transcript plus confidence where available.

Outputs:

- `model_clients/stt_client.py`
- STT unit and contract tests.

### 9. Embedding Integration Agent

Purpose: Builds embedding adapter for NVIDIA Llama Nemotron Embed VL 1B V2 and test mocks.

Responsibilities:

- Define `EmbeddingProvider` interface.
- Implement OpenAI-compatible embedding endpoint client.
- Support configurable model name, dimension, batch size, and timeout.
- Validate embedding dimensionality.
- Implement deterministic mock embeddings for tests.

Outputs:

- `model_clients/embedding_client.py`
- `model_clients/nvidia_embedding_client.py`
- Contract tests for vector shape and dimension.

### 10. Milvus Vector Store Agent

Purpose: Builds Milvus collection creation, upsert, query, metadata filtering, and health checks.

Responsibilities:

- Define `VectorStore` interface.
- Implement Milvus client adapter.
- Create collection schema with vector, chunk text, metadata fields.
- Support top-k search and filters.
- Support delete/reindex by document hash.

Outputs:

- `dataflows/milvus_store.py`
- Integration tests with Docker Milvus.

### 11. Retrieval and Reranking Agent

Purpose: Owns retrieval strategy after vector search.

Responsibilities:

- Implement top-k retrieval.
- Implement metadata filter handling.
- Implement optional reranker interface.
- Implement context window budgeting.
- Implement no-results behavior.

Outputs:

- `agents/retrieval/*`
- Retrieval quality tests.

### 12. Answer Generation Agent

Purpose: Builds prompt construction, LLM call, cited answer generation, and groundedness validation.

Responsibilities:

- Define `LLMProvider` interface.
- Implement Ollama/OpenAI-compatible chat client.
- Implement prompt templates.
- Implement citation validation.
- Implement no-evidence answer logic.
- Implement prompt injection defensive context handling.

Outputs:

- `model_clients/llm_client.py`
- `model_clients/ollama_client.py`
- `agents/answer/*`
- Answer quality tests.

### 13. API Service Agent

Purpose: Exposes local API endpoints.

Responsibilities:

- Implement FastAPI app.
- Add request/response schemas.
- Wire graphs into endpoints.
- Add health and metrics endpoints.
- Add API tests.

Outputs:

- `service/api.py`
- API contract tests.

### 14. Open WebUI Integration Agent

Purpose: Makes the product usable from Open WebUI.

Responsibilities:

- Provide Open WebUI integration options.
- Implement a tool or pipeline script where practical.
- Document how Open WebUI connects to local API and Ollama.
- Document RAG settings and limitations.

Outputs:

- `ui_integrations/openwebui_tools.py`
- `docs/openwebui_integration.md`

### 15. Local Runtime and DevOps Agent

Purpose: Makes the product deployable locally.

Responsibilities:

- Build Docker Compose for Milvus, Open WebUI, Ollama, and API.
- Provide `make` targets.
- Provide environment profiles.
- Provide startup health checks.

Outputs:

- `docker-compose.yml`
- `Makefile`
- `scripts/healthcheck.sh`
- Deployment docs.

### 16. Observability Agent

Purpose: Gives visibility into graph behavior.

Responsibilities:

- Add structured logs.
- Add run artifact persistence.
- Add per-node timing.
- Add retrieval score logging.
- Add optional tracing hooks.

Outputs:

- `observability/*`
- Graph run reports.

### 17. Security and Privacy Agent

Purpose: Protects local data, secrets, file ingestion, and prompt boundary.

Responsibilities:

- Implement secret redaction.
- Validate file paths and allowed extensions.
- Sanitize retrieved context.
- Prevent prompt injection instructions inside source docs from becoming system instructions.
- Add security tests.

Outputs:

- `utils/files.py`
- `utils/security.py`
- Security tests.

### 18. Documentation Agent

Purpose: Makes the product executable by humans.

Responsibilities:

- Write README, install, operations, testing, extension guides.
- Include examples.
- Include troubleshooting.

Outputs:

- `README.md`
- `docs/install.md`
- `docs/operations.md`
- `docs/testing.md`

### 19. Integration and Release Agent

Purpose: Assembles all modules into one release candidate.

Responsibilities:

- Merge subagent artifacts.
- Resolve interface mismatches.
- Run full test suite.
- Produce release notes.
- Confirm acceptance criteria.

Outputs:

- Release candidate branch.
- `docs/release_notes.md`
- Final test evidence.

## Agent communication protocol

Every build agent must produce a completion note with:

```text
Agent:
Task IDs completed:
Files changed:
Interfaces added or changed:
Tests added:
Commands run:
Known issues:
Follow-up tasks created:
```

## Dependency rules

- No provider-specific client should be called directly from a graph node without an interface.
- No graph node should perform file parsing and LLM generation in the same function.
- No test should require a real external API key unless explicitly marked as external integration.
- No code should assume NVIDIA, Milvus, Ollama, or Open WebUI is available during unit tests.
- No document content should be inserted into the system prompt without sanitization.

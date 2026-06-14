# Subagent Kanban Backlog

This backlog is designed to be copied into a Kanban board. Initial status for all tasks is `Backlog` unless changed by the orchestrator.

## Status values

- Backlog
- Ready
- In Progress
- Blocked
- Review
- Test
- Done

## Priority values

- P0: Required for minimum viable product.
- P1: Required for robust local release.
- P2: Useful enhancement.

## Build backlog

### EPIC A - Product foundation

#### VRAG-A001 - Create repository scaffold

- Owner: Repository Scaffold Agent
- Priority: P0
- Status: Backlog
- Dependencies: None
- Description: Create the Python package, standard directories, `pyproject.toml`, Makefile, `.env.example`, and placeholder tests.
- Deliverables:
  - Repository tree under `src/voice_rag_agents`.
  - `tests/unit/test_package_import.py`.
  - `make test` target.
- Acceptance criteria:
  - Package imports successfully.
  - `make test` runs without external services.
  - README has local development quickstart placeholder.
- Required tests:
  - Import test.
  - CLI or module smoke test if CLI is created.

#### VRAG-A002 - Define default configuration system

- Owner: Repository Scaffold Agent
- Priority: P0
- Dependencies: VRAG-A001
- Description: Implement config defaults and environment variable overrides.
- Deliverables:
  - `default_config.py`
  - `config/settings.py`
  - `.env.example`
- Acceptance criteria:
  - Defaults load without `.env`.
  - Env vars override default values.
  - Config can select mock, local, integration profiles.
- Required tests:
  - Env override test.
  - Missing optional secret test.
  - Invalid enum value test.

#### VRAG-A003 - Write product requirements and ADRs

- Owner: Product Definition Agent
- Priority: P0
- Dependencies: None
- Description: Convert blueprint into repository documentation.
- Deliverables:
  - `docs/product_requirements.md`
  - `docs/adr/0001-langgraph-modular-architecture.md`
- Acceptance criteria:
  - Work statement, scope, user journeys, and acceptance criteria documented.
  - ADR explains provider-adapter and graph-first design.
- Required tests:
  - Documentation link check if available.

### EPIC B - Core interfaces and schemas

#### VRAG-B001 - Define domain schemas

- Owner: LangGraph Core Agent
- Priority: P0
- Dependencies: VRAG-A001
- Description: Define typed records for documents, chunks, embeddings, retrieval results, citations, errors, and graph state.
- Deliverables:
  - `agents/schemas.py`
  - `graph/states.py`
  - `dataflows/vector_records.py`
- Acceptance criteria:
  - Schemas are typed and serializable.
  - Graph state supports ingestion, query, admin, eval flows.
- Required tests:
  - Serialization tests.
  - Required field validation tests.

#### VRAG-B002 - Define provider interfaces

- Owner: Solution Architecture Agent
- Priority: P0
- Dependencies: VRAG-B001
- Description: Define protocols or abstract classes for STT, embeddings, vector store, retriever, reranker, LLM, prompt builder, citation builder, and evaluator.
- Deliverables:
  - `model_clients/interfaces.py`
  - `dataflows/interfaces.py`
  - `agents/interfaces.py`
- Acceptance criteria:
  - Interfaces have clear input/output types.
  - Mocks can implement all interfaces.
- Required tests:
  - Type-checking target if configured.
  - Mock conformance tests.

#### VRAG-B003 - Implement deterministic mock providers

- Owner: Repository Scaffold Agent
- Priority: P0
- Dependencies: VRAG-B002
- Description: Create mock STT, embedding, vector store, and LLM providers for unit and graph tests.
- Deliverables:
  - `model_clients/mock_clients.py`
  - `dataflows/mock_vector_store.py`
- Acceptance criteria:
  - No external services required.
  - Mock embedding is deterministic and configurable dimension.
  - Mock vector store supports upsert/search/filter.
- Required tests:
  - Mock embedding determinism.
  - Mock vector search returns expected chunks.
  - Mock LLM no-evidence response.

### EPIC C - LangGraph orchestration

#### VRAG-C001 - Implement graph conditional logic

- Owner: LangGraph Core Agent
- Priority: P0
- Dependencies: VRAG-B001
- Description: Implement route functions for request type, ingestion errors, STT confidence, no retrieval results, citation validation, and retry decisions.
- Deliverables:
  - `graph/conditional_logic.py`
- Acceptance criteria:
  - All route functions are pure and unit-tested.
  - Routes return explicit node names or END.
- Required tests:
  - Request routing tests.
  - Error routing tests.
  - No evidence routing tests.

#### VRAG-C002 - Implement QueryGraph skeleton

- Owner: LangGraph Core Agent
- Priority: P0
- Dependencies: VRAG-B003, VRAG-C001
- Description: Build QueryGraph using mock providers and placeholder node implementations.
- Deliverables:
  - `graph/query_graph.py`
- Acceptance criteria:
  - Graph accepts typed text query.
  - Graph returns cited answer from mock retrieval.
  - Graph handles no retrieval result.
- Required tests:
  - Happy path query graph test.
  - No results graph test.
  - LLM failure route test.

#### VRAG-C003 - Implement IngestionGraph skeleton

- Owner: LangGraph Core Agent
- Priority: P0
- Dependencies: VRAG-B003, VRAG-C001
- Description: Build IngestionGraph using mock providers.
- Deliverables:
  - `graph/ingestion_graph.py`
- Acceptance criteria:
  - Graph ingests sample document into mock vector store.
  - Graph records ingestion report.
- Required tests:
  - Happy path ingestion graph test.
  - Unsupported file route test.
  - Embedding failure route test.

#### VRAG-C004 - Implement SupervisorGraph

- Owner: LangGraph Core Agent
- Priority: P0
- Dependencies: VRAG-C002, VRAG-C003
- Description: Build the graph that routes requests to ingestion, query, admin, or evaluation subgraphs.
- Deliverables:
  - `graph/supervisor_graph.py`
- Acceptance criteria:
  - Correct subgraph is selected from request type.
  - Subgraph outputs are summarized consistently.
- Required tests:
  - Route to ingestion.
  - Route to query.
  - Unknown request type returns actionable error.

#### VRAG-C005 - Implement checkpoint and run artifact support

- Owner: LangGraph Core Agent
- Priority: P1
- Dependencies: VRAG-C002, VRAG-C003
- Description: Add checkpointer hooks and persist graph run artifacts.
- Deliverables:
  - `graph/checkpointer.py`
  - `observability/run_artifacts.py`
- Acceptance criteria:
  - Long-running ingestion can save progress.
  - Run artifacts include node status, timings, warnings, errors.
- Required tests:
  - Checkpoint create/resume simulation.
  - Artifact write/read test.

### EPIC D - Ingestion and dataflows

#### VRAG-D001 - Implement safe file loader

- Owner: Data Ingestion Agent
- Priority: P0
- Dependencies: VRAG-B001
- Description: Load files from allowed directories and prevent path traversal.
- Deliverables:
  - `dataflows/loaders.py`
  - `utils/files.py`
- Acceptance criteria:
  - Allows supported file types.
  - Blocks unsafe paths.
  - Emits document records with source metadata.
- Required tests:
  - Load `.md` and `.txt` fixtures.
  - Reject `../` traversal.
  - Reject unsupported extension.

#### VRAG-D002 - Implement document parsers

- Owner: Data Ingestion Agent
- Priority: P0
- Dependencies: VRAG-D001
- Description: Parse Markdown, text, and simple transcript documents. Add PDF parser if dependency is acceptable.
- Deliverables:
  - `dataflows/parsers.py`
- Acceptance criteria:
  - Parser returns normalized document text.
  - Parser preserves headings where possible.
  - Parser errors are captured, not fatal to entire batch.
- Required tests:
  - Markdown heading extraction.
  - Transcript parsing.
  - Bad file quarantine behavior.

#### VRAG-D003 - Implement chunker

- Owner: Chunking and Metadata Agent
- Priority: P0
- Dependencies: VRAG-D002
- Description: Implement heading-aware chunking with token budget and overlap.
- Deliverables:
  - `dataflows/chunking.py`
- Acceptance criteria:
  - Default chunk size and overlap are configurable.
  - Chunks preserve source, sequence, section, and text.
  - Chunk IDs are stable for unchanged content.
- Required tests:
  - Small doc produces one chunk.
  - Long doc produces multiple overlapping chunks.
  - Heading sections are preserved.

#### VRAG-D004 - Implement metadata extractor

- Owner: Chunking and Metadata Agent
- Priority: P0
- Dependencies: VRAG-D002
- Description: Extract metadata from file path, front matter, transcript headers, and optional patterns.
- Deliverables:
  - `dataflows/metadata.py`
- Acceptance criteria:
  - Metadata includes source file, title, created/modified time, content hash, section, tags where available.
  - Meeting notes extract date and attendees when present.
- Required tests:
  - Meeting date extraction.
  - Attendee extraction.
  - Missing metadata safe defaults.

### EPIC E - Model clients

#### VRAG-E001 - Implement STT provider interface and mock

- Owner: STT Integration Agent
- Priority: P0
- Dependencies: VRAG-B002
- Description: Implement STT interface and mock provider.
- Deliverables:
  - `model_clients/stt_client.py`
- Acceptance criteria:
  - `transcribe(audio)` returns transcript, confidence, provider metadata.
  - Mock can return configurable transcript.
- Required tests:
  - Mock STT returns text.
  - Missing audio returns validation error.

#### VRAG-E002 - Implement local command STT provider

- Owner: STT Integration Agent
- Priority: P1
- Dependencies: VRAG-E001
- Description: Implement command-line STT adapter for Cipher or Whisper.cpp style binary execution.
- Deliverables:
  - `model_clients/local_stt_command.py`
- Acceptance criteria:
  - Command path and model path are config-driven.
  - Timeout and stderr are handled.
  - Tests use a fake command script, not real STT.
- Required tests:
  - Fake command success.
  - Timeout failure.
  - Non-zero exit handling.

#### VRAG-E003 - Implement embedding provider and NVIDIA adapter

- Owner: Embedding Integration Agent
- Priority: P0
- Dependencies: VRAG-B002
- Description: Implement OpenAI-compatible embedding client for NVIDIA Llama Nemotron Embed VL 1B V2.
- Deliverables:
  - `model_clients/embedding_client.py`
  - `model_clients/nvidia_embedding_client.py`
- Acceptance criteria:
  - Supports text batch embedding.
  - Supports configurable dimension expectation.
  - Validates response shape.
  - Tests do not require a live NVIDIA endpoint.
- Required tests:
  - Mock HTTP embedding response.
  - Dimension mismatch failure.
  - Batch request shape.

#### VRAG-E004 - Implement LLM provider and Ollama adapter

- Owner: Answer Generation Agent
- Priority: P0
- Dependencies: VRAG-B002
- Description: Implement OpenAI-compatible chat client and Ollama profile.
- Deliverables:
  - `model_clients/llm_client.py`
  - `model_clients/ollama_client.py`
- Acceptance criteria:
  - Supports system, user, and context messages.
  - Supports timeout and retry.
  - Tests use mock HTTP server or monkeypatch.
- Required tests:
  - Chat request shape.
  - Timeout handling.
  - No-evidence prompt response using mock LLM.

### EPIC F - Milvus and retrieval

#### VRAG-F001 - Implement vector store interface

- Owner: Milvus Vector Store Agent
- Priority: P0
- Dependencies: VRAG-B002
- Description: Define vector store behavior for collection create, upsert, search, delete, health.
- Deliverables:
  - `dataflows/vector_store.py`
- Acceptance criteria:
  - Interface supports metadata filters and output fields.
  - Mock vector store conforms.
- Required tests:
  - Interface conformance via mock.

#### VRAG-F002 - Implement Milvus adapter

- Owner: Milvus Vector Store Agent
- Priority: P0
- Dependencies: VRAG-F001, VRAG-E003
- Description: Implement Milvus collection schema, upsert, search, filter, and health check.
- Deliverables:
  - `dataflows/milvus_store.py`
- Acceptance criteria:
  - Creates collection with vector and metadata fields.
  - Upserts chunk text, vector, source metadata, and hashes.
  - Searches by vector with top-k and optional metadata filter.
- Required tests:
  - Unit tests with client mock.
  - Integration test with local Milvus container.

#### VRAG-F003 - Implement retrieval service

- Owner: Retrieval and Reranking Agent
- Priority: P0
- Dependencies: VRAG-F001
- Description: Implement query embedding to top-k retrieval with metadata filtering.
- Deliverables:
  - `agents/retrieval/retriever.py`
- Acceptance criteria:
  - Returns ranked results with scores, chunk text, metadata, citation IDs.
  - Handles empty result set.
- Required tests:
  - Top-k order.
  - Metadata filter reduces results.
  - Empty results produce no-evidence route.

#### VRAG-F004 - Implement context assembler

- Owner: Retrieval and Reranking Agent
- Priority: P0
- Dependencies: VRAG-F003
- Description: Convert retrieved chunks into context packet within token budget.
- Deliverables:
  - `agents/retrieval/context_assembler.py`
- Acceptance criteria:
  - Includes citation labels.
  - Includes source metadata.
  - Respects max context tokens.
- Required tests:
  - Context contains expected chunks.
  - Over-budget context is trimmed safely.
  - Citations map to chunk IDs.

### EPIC G - Answer generation

#### VRAG-G001 - Implement answer prompt builder

- Owner: Answer Generation Agent
- Priority: P0
- Dependencies: VRAG-F004
- Description: Build prompt template for grounded answer generation.
- Deliverables:
  - `agents/answer/prompt_builder.py`
- Acceptance criteria:
  - System prompt instructs model to answer only from retrieved context.
  - Retrieved document text is treated as untrusted data.
  - No-evidence behavior is explicit.
- Required tests:
  - Prompt contains context and question.
  - Prompt injection string remains data, not instruction.

#### VRAG-G002 - Implement citation builder and validator

- Owner: Answer Generation Agent
- Priority: P0
- Dependencies: VRAG-F004, VRAG-G001
- Description: Build citation format and validate answer citations.
- Deliverables:
  - `agents/answer/citations.py`
- Acceptance criteria:
  - Every citation maps to retrieved chunk.
  - Invalid citation is detected.
  - Missing citation can trigger regeneration or no-evidence route.
- Required tests:
  - Valid citations pass.
  - Missing citation fails.
  - Unknown citation ID fails.

#### VRAG-G003 - Implement answer node

- Owner: Answer Generation Agent
- Priority: P0
- Dependencies: VRAG-E004, VRAG-G001, VRAG-G002
- Description: Implement answer generation graph node.
- Deliverables:
  - `agents/answer/generator.py`
- Acceptance criteria:
  - Uses LLM provider interface.
  - Returns answer, citations, warnings, quality metadata.
  - Handles no context.
- Required tests:
  - Cited answer path.
  - No-evidence path.
  - LLM failure path.

### EPIC H - API and UI integration

#### VRAG-H001 - Implement FastAPI service

- Owner: API Service Agent
- Priority: P0
- Dependencies: VRAG-C002, VRAG-C003, VRAG-C004
- Description: Expose graph operations through local API endpoints.
- Deliverables:
  - `service/api.py`
  - `service/schemas.py`
- Acceptance criteria:
  - `/health`, `/ingest`, `/query`, `/eval/run` endpoints exist.
  - Endpoints use dependency injection for providers.
  - API can run in mock mode.
- Required tests:
  - API health test.
  - API query test with mock providers.
  - API ingest test with sample document.

#### VRAG-H002 - Implement Open WebUI integration guide and tool

- Owner: Open WebUI Integration Agent
- Priority: P1
- Dependencies: VRAG-H001
- Description: Provide Open WebUI integration path through tool/pipeline/local API.
- Deliverables:
  - `ui_integrations/openwebui_tools.py`
  - `docs/openwebui_integration.md`
- Acceptance criteria:
  - Documents how to connect Open WebUI to local API.
  - Provides example tool function or pipeline.
  - Documents configuration vs customization.
- Required tests:
  - Tool function unit test.
  - Documentation smoke check.

### EPIC I - Deployment and operations

#### VRAG-I001 - Build Docker Compose stack

- Owner: Local Runtime and DevOps Agent
- Priority: P0
- Dependencies: VRAG-H001, VRAG-F002
- Description: Provide local deployment for API, Milvus, Ollama, Open WebUI, and optional supporting services.
- Deliverables:
  - `docker-compose.yml`
  - `.env.example`
- Acceptance criteria:
  - `docker compose up` starts core services or clearly marks optional services.
  - Service URLs align with config defaults.
- Required tests:
  - Compose config validation.
  - Healthcheck script.

#### VRAG-I002 - Add Makefile targets

- Owner: Local Runtime and DevOps Agent
- Priority: P0
- Dependencies: VRAG-A001
- Description: Add common commands.
- Deliverables:
  - `Makefile`
- Acceptance criteria:
  - `make test`, `make integration-test`, `make eval`, `make lint`, `make run-api`, `make compose-up`, `make health` exist.
- Required tests:
  - CI invokes key targets.

#### VRAG-I003 - Implement observability layer

- Owner: Observability Agent
- Priority: P1
- Dependencies: VRAG-C002, VRAG-C003
- Description: Add structured logs, timings, run IDs, and retrieval diagnostics.
- Deliverables:
  - `observability/logging.py`
  - `observability/tracing.py`
- Acceptance criteria:
  - Every graph run has a run ID.
  - Node durations are logged.
  - Retrieval scores and selected chunk IDs are logged.
- Required tests:
  - Log redaction test.
  - Run artifact content test.

### EPIC J - Security and privacy

#### VRAG-J001 - Implement file safety controls

- Owner: Security and Privacy Agent
- Priority: P0
- Dependencies: VRAG-D001
- Description: Enforce safe file ingestion boundaries.
- Deliverables:
  - `utils/files.py`
  - Security tests.
- Acceptance criteria:
  - Path traversal blocked.
  - Unsupported file types blocked.
  - Oversized files handled by config policy.
- Required tests:
  - Path traversal.
  - Symlink escape if relevant.
  - File size limit.

#### VRAG-J002 - Implement secret redaction

- Owner: Security and Privacy Agent
- Priority: P0
- Dependencies: VRAG-A002
- Description: Redact secrets from logs, run artifacts, errors, and reports.
- Deliverables:
  - `utils/security.py`
- Acceptance criteria:
  - API keys and tokens are not logged.
  - `.env.example` contains placeholders only.
- Required tests:
  - Secret pattern redaction.
  - Error reporting does not leak config secret.

#### VRAG-J003 - Implement prompt injection mitigation

- Owner: Security and Privacy Agent
- Priority: P1
- Dependencies: VRAG-G001
- Description: Treat retrieved text as untrusted data and prevent document instructions from overriding system instructions.
- Deliverables:
  - `agents/answer/context_sanitizer.py`
- Acceptance criteria:
  - Prompt builder isolates context.
  - Injection markers are flagged.
  - Answer generator remains grounded.
- Required tests:
  - Malicious document fixture.
  - Prompt injection does not change answer policy.

### EPIC K - Documentation

#### VRAG-K001 - Write installation guide

- Owner: Documentation Agent
- Priority: P0
- Dependencies: VRAG-I001
- Description: Document local setup from scratch.
- Deliverables:
  - `docs/install.md`
- Acceptance criteria:
  - Intern-level instructions.
  - Includes prerequisites, commands, expected output, troubleshooting.
- Required tests:
  - Documentation command review.

#### VRAG-K002 - Write operations guide

- Owner: Documentation Agent
- Priority: P1
- Dependencies: VRAG-I003
- Description: Document run, health, reindex, backup, restore, eval, troubleshooting.
- Deliverables:
  - `docs/operations.md`
- Acceptance criteria:
  - Contains day-2 operating procedures.
  - Contains known failure modes.

#### VRAG-K003 - Write extension guide

- Owner: Documentation Agent
- Priority: P1
- Dependencies: VRAG-B002
- Description: Document how to add a provider, graph node, file parser, reranker, or eval.
- Deliverables:
  - `docs/extending.md`
- Acceptance criteria:
  - Includes examples and test requirements.

### EPIC L - Release integration

#### VRAG-L001 - Integrate modules into release candidate

- Owner: Integration and Release Agent
- Priority: P0
- Dependencies: All P0 build tasks
- Description: Wire modules, resolve contracts, run tests, and produce release candidate.
- Deliverables:
  - Integrated branch.
  - `docs/release_notes.md`
- Acceptance criteria:
  - Unit and graph tests pass.
  - Mock mode API works.
  - Sample ingest/query demo works.

#### VRAG-L002 - Run acceptance gate

- Owner: Integration and Release Agent
- Priority: P0
- Dependencies: VRAG-L001, testing workforce gates
- Description: Run final acceptance criteria and capture evidence.
- Deliverables:
  - `docs/acceptance_evidence.md`
- Acceptance criteria:
  - All P0 tests pass or blockers documented.
  - Known limitations documented.
  - Release notes include setup, test evidence, and risks.

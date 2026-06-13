# Work Statement: Work, Workforce, Workbench

## Single statement of work

Build a modular, LangGraph-orchestrated, locally deployable voice-to-answer knowledge assistant that converts speech or text into a grounded query, embeds that query and source knowledge with OpenRoute NVIDIA Llama Nemotron Embed VL 1B V2, stores and searches vectorized knowledge in Milvus, generates cited answers using a locally hosted LLM, and continuously validates the product with an independent automated testing workforce.

## The three dimensions

### 1. Work

The work is the product to be built.

The product is a reusable Python package plus deployable local stack called `voice_rag_agents`. It provides a LangGraph-based orchestration layer for voice RAG, plus adapters for Open WebUI, Milvus, Ollama, NVIDIA embedding endpoints, local STT engines, and automated evaluations.

#### Product capabilities

| Capability | Description |
|---|---|
| Voice input | Accept voice from UI or API and route it to local STT. |
| Text input | Accept typed query directly. |
| Local STT | Convert speech to text using Cipher, Whisper.cpp, or compatible local STT provider. |
| Knowledge ingestion | Load PDFs, Markdown, text, meeting transcripts, and structured notes. |
| Chunking | Split content by headings, paragraphs, semantic boundaries, token budget, and overlap. |
| Embedding | Embed chunks and queries using NVIDIA Llama Nemotron Embed VL 1B V2. |
| Vector storage | Store vectors, text, and metadata in Milvus. |
| Metadata filtering | Filter by source, date, person, project, document type, and tags. |
| Retrieval | Search top-k similar chunks and optionally rerank or filter. |
| Context assembly | Build a grounded context packet with citations and metadata. |
| Local answer generation | Use a local LLM through Ollama or OpenAI-compatible endpoint. |
| Citation validation | Ensure answer references retrieved source chunks. |
| UI integration | Support Open WebUI integration and a local FastAPI endpoint. |
| Observability | Log graph runs, node status, timings, retrieval scores, and failure modes. |
| Evaluation | Run ongoing retrieval and answer quality tests. |

#### Primary user journeys

1. User uploads or syncs documents.
2. System parses, chunks, embeds, and stores them in Milvus.
3. User asks a question by voice.
4. Local STT converts speech to text.
5. Query is normalized and embedded.
6. Milvus returns matching chunks with metadata.
7. Local LLM generates a cited answer.
8. UI displays answer, sources, and follow-up suggestions.

#### Product boundaries

In scope:

- Local-first RAG orchestration.
- Modular adapters for STT, embeddings, vector search, LLM, UI, and evals.
- LangGraph graph construction, state, checkpoints, and conditional routing.
- Automated test and evaluation platform.
- Docker Compose local deployment.

Out of scope for first release:

- Enterprise SSO.
- Multi-tenant role-based access control beyond basic local user separation.
- Cloud-scale Kubernetes production hardening.
- Full mobile app.
- Real-time streaming voice conversation beyond request/response STT.

## 2. Workforce

The workforce is the set of build agents, subagents, and test agents that will carry out the work.

### Build workforce

The build workforce is coordinated by a Product Orchestrator Agent. It contains specialists for architecture, graph engineering, data ingestion, embeddings, vector storage, retrieval, LLM generation, UI integration, deployment, documentation, observability, and security.

### Testing workforce

The testing workforce is separate and adversarial. It receives the work definition and product artifacts, derives independent test cases, builds automated tests, and blocks release if acceptance gates fail.

### Workforce operating model

- Every agent receives a bounded task and produces an artifact.
- Every artifact has a contract and acceptance criteria.
- Subagents do not rewrite each other's modules without coordinating through the Orchestrator Agent.
- The Testing Orchestrator Agent owns the test plan and is independent of the Build Orchestrator Agent.
- The Release Manager Agent assembles work only after build and test gates pass.

## 3. Workbench

The workbench is the environment, tools, runtime services, and controls needed to complete the work.

### Required workbench areas

| Area | Required assets |
|---|---|
| Source control | Git repository, branch protection, pull request workflow. |
| Runtime | Python 3.11+, Docker, Docker Compose. |
| Orchestration | LangGraph and LangChain-compatible runtime. |
| Vector database | Milvus standalone local deployment and client SDK. |
| Local LLM | Ollama and at least one local chat model. |
| Embedding service | NVIDIA embedding endpoint or mock-compatible local service. |
| STT | Cipher, Whisper.cpp, or compatible local STT provider. |
| UI | Open WebUI plus optional lightweight local demo UI. |
| API | FastAPI orchestration service. |
| Observability | Structured logs, traces, run artifacts, optional LangSmith. |
| Testing | Pytest, mocks, integration containers, RAG eval fixtures, CI. |
| Security | Secret management, `.env.example`, redaction, file safety controls. |

## Success criteria

The work is successful when a new developer can:

1. Clone the repository.
2. Start the local stack.
3. Ingest sample meeting notes.
4. Ask a voice or text question.
5. Receive a grounded answer with citations.
6. Run unit tests without external services.
7. Run integration tests with Docker Compose.
8. Run RAG evaluation and see quality metrics.
9. Swap STT, embedding, vector store, or LLM provider by configuration.
10. Add a new graph node without rewriting the entire product.

## Quality attributes

| Attribute | Target |
|---|---|
| Modularity | All external dependencies behind interfaces. |
| Flexibility | Graph nodes can be inserted, disabled, replaced, or routed conditionally. |
| Local-first operation | Core local demo works without mandatory cloud LLM. |
| Groundedness | Answers must use retrieved context or declare insufficient evidence. |
| Testability | Node-level, graph-level, integration, and eval tests are automated. |
| Traceability | Every answer links back to chunks and source metadata. |
| Recoverability | Ingestion can resume or be safely rerun. |
| Maintainability | Package structure is clear and resembles a known modular multi-agent pattern. |

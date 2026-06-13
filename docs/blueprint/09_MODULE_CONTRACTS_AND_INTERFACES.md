# Module Contracts and Interfaces

## Purpose

This file defines the contracts between modules so subagents can work independently and the integration agent can assemble the product safely.

## STT provider contract

```python
class STTResult(BaseModel):
    transcript: str
    confidence: float | None = None
    language: str | None = None
    duration_seconds: float | None = None
    provider_metadata: dict = {}

class STTProvider(Protocol):
    def transcribe(self, audio_path: str) -> STTResult:
        ...
```

Rules:

- Provider must not return empty transcript as success.
- Provider must handle missing audio path.
- Provider must expose timeout configuration.
- Provider must not require microphone access in tests.

## Embedding provider contract

```python
class EmbeddingRequest(BaseModel):
    texts: list[str]
    model: str | None = None
    input_type: Literal['query', 'document'] = 'document'

class EmbeddingResult(BaseModel):
    vectors: list[list[float]]
    model: str
    dimension: int
    token_usage: dict | None = None
    provider_metadata: dict = {}

class EmbeddingProvider(Protocol):
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        ...
```

Rules:

- Number of vectors must equal number of input texts.
- All vectors must have the same dimension.
- Dimension must match config and Milvus schema.
- Query and document embeddings should use the same model unless explicitly configured otherwise.

## Vector store contract

```python
class VectorRecord(BaseModel):
    id: str
    document_id: str
    chunk_id: str
    chunk_text: str
    vector: list[float]
    metadata: dict

class SearchRequest(BaseModel):
    query_vector: list[float]
    top_k: int = 5
    filters: dict | None = None
    output_fields: list[str] = ['chunk_text', 'metadata']

class SearchResult(BaseModel):
    id: str
    chunk_id: str
    chunk_text: str
    score: float
    metadata: dict

class VectorStore(Protocol):
    def health(self) -> dict: ...
    def ensure_collection(self, name: str, dimension: int) -> None: ...
    def upsert(self, collection: str, records: list[VectorRecord]) -> dict: ...
    def search(self, collection: str, request: SearchRequest) -> list[SearchResult]: ...
    def delete_by_document_id(self, collection: str, document_id: str) -> dict: ...
```

## Milvus collection schema

Recommended fields:

| Field | Type | Purpose |
|---|---|---|
| `id` | VarChar or Int64 primary key | Unique vector record ID. |
| `document_id` | VarChar | Stable document hash or ID. |
| `chunk_id` | VarChar | Stable chunk ID. |
| `embedding` | FloatVector | Vector embedding. |
| `chunk_text` | VarChar | Text used for answer context. |
| `source_file` | VarChar | Original file path/name. |
| `source_title` | VarChar | Document title. |
| `section` | VarChar | Heading or section. |
| `created_date` | VarChar | ISO date if available. |
| `modified_date` | VarChar | ISO date if available. |
| `content_hash` | VarChar | Hash for dedup/reindex. |
| `metadata_json` | JSON | Flexible metadata. |

Implementation may adapt field types to Milvus SDK constraints, but the data must be retrievable with the search result.

## LLM provider contract

```python
class ChatMessage(BaseModel):
    role: Literal['system', 'user', 'assistant']
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None

class ChatResult(BaseModel):
    content: str
    model: str
    usage: dict | None = None
    provider_metadata: dict = {}

class LLMProvider(Protocol):
    def chat(self, request: ChatRequest) -> ChatResult:
        ...
```

Rules:

- Provider errors must become structured graph errors.
- Unit tests must use mock provider.
- Local Ollama adapter should use OpenAI-compatible chat shape if possible.

## Retriever contract

```python
class Retriever(Protocol):
    def retrieve(self, query: str, filters: dict | None = None, top_k: int = 5) -> list[SearchResult]:
        ...
```

Rules:

- Retriever may embed query internally or receive vector from graph state depending on implementation.
- In the LangGraph implementation, keep query embedding as its own node for traceability.

## Prompt builder contract

```python
class PromptBuildRequest(BaseModel):
    question: str
    context_chunks: list[SearchResult]
    conversation_summary: str | None = None
    instructions: dict = {}

class PromptBuildResult(BaseModel):
    messages: list[ChatMessage]
    citation_map: dict[str, str]

class PromptBuilder(Protocol):
    def build(self, request: PromptBuildRequest) -> PromptBuildResult:
        ...
```

Rules:

- Source chunks must be clearly delimited as untrusted context.
- The prompt must instruct the LLM to answer only from context.
- The prompt must instruct no-evidence behavior.
- Citation labels must map to chunk IDs.

## Citation validator contract

```python
class CitationValidationResult(BaseModel):
    valid: bool
    missing_citations: list[str] = []
    unknown_citations: list[str] = []
    warnings: list[str] = []

class CitationValidator(Protocol):
    def validate(self, answer: str, citation_map: dict[str, str]) -> CitationValidationResult:
        ...
```

## API request/response contracts

### POST `/ingest`

Request:

```json
{
  "paths": ["./data/input/meeting_notes.md"],
  "collection": "voice_rag_chunks",
  "reindex": false,
  "metadata": {
    "project": "orion"
  }
}
```

Response:

```json
{
  "run_id": "...",
  "status": "success",
  "documents_loaded": 1,
  "chunks_created": 4,
  "vectors_upserted": 4,
  "warnings": [],
  "errors": []
}
```

### POST `/query`

Request:

```json
{
  "text": "What risks were raised about third-party APIs?",
  "audio_path": null,
  "collection": "voice_rag_chunks",
  "top_k": 5,
  "filters": {
    "project": "orion"
  }
}
```

Response:

```json
{
  "run_id": "...",
  "status": "success",
  "transcript": null,
  "answer": "The notes identify third-party API rate limits as a risk to analytics. [S1]",
  "citations": [
    {
      "label": "S1",
      "chunk_id": "meeting_notes_chunk_002",
      "source_file": "meeting_notes.md",
      "section": "Risks and Blockers"
    }
  ],
  "retrieval_results": [
    {
      "chunk_id": "meeting_notes_chunk_002",
      "score": 0.86,
      "source_file": "meeting_notes.md"
    }
  ],
  "warnings": [],
  "errors": []
}
```

## Ingestion records

### DocumentRecord

```json
{
  "document_id": "sha256:...",
  "source_file": "meeting_notes.md",
  "source_type": "markdown",
  "title": "Product Roadmap Sync",
  "text": "...",
  "metadata": {
    "meeting_date": "2026-05-20",
    "attendees": ["Alice", "Bob"]
  }
}
```

### ChunkRecord

```json
{
  "chunk_id": "meeting_notes_0002",
  "document_id": "sha256:...",
  "sequence": 2,
  "section": "Risks and Blockers",
  "text": "Third-party API rate limits may impact analytics...",
  "token_count": 84,
  "metadata": {
    "project": "Orion",
    "source_file": "meeting_notes.md"
  }
}
```

## Error contract

```json
{
  "code": "EMBEDDING_DIMENSION_MISMATCH",
  "message": "Embedding dimension 1024 does not match configured collection dimension 2048.",
  "node": "validate_embeddings",
  "retryable": false,
  "details": {
    "expected": 2048,
    "actual": 1024
  }
}
```

## Provider adapter requirements

Every provider adapter must expose:

- Constructor from `Settings`.
- Health check where possible.
- Timeout handling.
- Retry behavior if configured.
- Structured errors.
- Unit tests with mocks.
- Documentation for configuration.

## Configuration vs customization

Configuration:

- Model names.
- Provider URLs.
- API keys.
- Chunk sizes.
- Retrieval top-k.
- Collection name.
- Index type.
- Timeouts.
- Runtime profile.

Customization:

- New graph nodes.
- New provider adapters.
- New reranking strategy.
- New UI integration.
- New document parser.
- New evaluation metric.
- New security policy.

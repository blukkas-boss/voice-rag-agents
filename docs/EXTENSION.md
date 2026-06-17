# Extending voice_rag_agents

The system is built around **frozen provider interfaces**. To add a provider,
implement the interface and register it in the provider factory — no graph
changes needed.

## Add a new provider

1. Implement the relevant protocol from:
   - `model_clients/interfaces.py` — `STTProvider`, `EmbeddingProvider`, `LLMProvider`
   - `dataflows/interfaces.py` — `VectorStore`
   - `agents/interfaces.py` — `Retriever`, `Reranker`, `PromptBuilder`, `CitationValidator`, `EvaluationScorer`

2. Add it to `model_clients/provider_factory.py`, keyed off `settings.profile`
   or a new setting.

3. Add a unit test (mocked I/O) and a contract test (response shape). Tests
   must not require live services.

Example — a new vector store:

```python
class MyVectorStore:
    def health(self) -> dict: ...
    def ensure_collection(self, name: str, dimension: int) -> None: ...
    def upsert(self, collection: str, records: list[VectorRecord]) -> dict: ...
    def search(self, collection: str, request: SearchRequest) -> list[SearchResult]: ...
    def delete_by_document_id(self, collection: str, document_id: str) -> dict: ...
```

Then in `get_vector_store()` return `MyVectorStore(...)` for your profile.

## Add a document format

Extend `dataflows/document_loader.py`: add the extension to the loader registry
with a parse function. Keep parsing inside the loader (graph nodes stay clean).

## Interface freeze policy

Changing a frozen interface requires: an impact note, a backward-compat plan,
and updated tests. Prefer adding new optional methods over changing existing
signatures.

## Guardrails (enforced at review)

1. No monolith — keep module boundaries.
2. No provider SDK calls inside graph nodes — adapters only.
3. Unit tests never require external services.
4/5. Never commit or log secrets (`service/security.redact_secrets`).
6. Retrieved text is untrusted data, never instructions
   (`service/security.neutralize_injection`).
7. No unsupported answers on retrieval failure (no-evidence fallback).

"""Retrieval + context assembly + citation validation.

Wires real providers (EmbeddingProvider, VectorStore) into the query
pipeline. Replaces the mock-only stubs in the graph nodes.
"""

from __future__ import annotations

import hashlib

from voice_rag_agents.agents.schemas import Citation
from voice_rag_agents.dataflows.vector_records import (
    SearchRequest,
    SearchResult,
    VectorRecord,
)
from voice_rag_agents.model_clients.interfaces import (
    EmbeddingProvider,
    EmbeddingRequest,
)
from voice_rag_agents.dataflows.interfaces import VectorStore


def _make_chunk_id(text: str, source: str, index: int) -> str:
    digest = hashlib.sha256(f"{source}:{index}:{text[:64]}".encode()).hexdigest()[:12]
    return f"chunk-{digest}"


def _make_doc_id(source: str) -> str:
    return f"doc-{hashlib.sha256(source.encode()).hexdigest()[:12]}"


def retrieve(
    query: str,
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStore,
    collection: str,
    top_k: int = 5,
    filters: dict | None = None,
) -> list[SearchResult]:
    """Embed *query* and search the vector store.

    Returns a list of SearchResult (may be empty → no-evidence path).
    """
    req = EmbeddingRequest(texts=[query], input_type="query")
    emb_result = embedding_provider.embed(req)
    if not emb_result.vectors:
        return []

    search_req = SearchRequest(
        query_vector=emb_result.vectors[0],
        top_k=top_k,
        filters=filters,
    )
    return vector_store.search(collection, search_req)


def assemble_context(results: list[SearchResult]) -> tuple[str, list[Citation]]:
    """Build a context string + citation list from search results.

    Returns ``(context_text, citations)``.
    """
    if not results:
        return "", []

    parts: list[str] = []
    citations: list[Citation] = []

    for i, r in enumerate(results):
        label = f"S{i + 1}"
        parts.append(f"[{label}] {r.chunk_text}")
        citations.append(
            Citation(
                label=label,
                chunk_id=r.chunk_id,
                source_file=r.metadata.get("source_file", r.document_id),
                section=r.metadata.get("section", ""),
                text=r.chunk_text[:200],
            )
        )

    return "\n\n".join(parts), citations


def chunk_to_vector_records(
    chunks: list[dict],
    embedding_provider: EmbeddingProvider,
) -> tuple[list[VectorRecord], list[dict]]:
    """Embed chunks and convert to VectorRecords for upsert.

    Returns ``(vector_records, embedding_records)``.
    """
    texts = [c["text"] for c in chunks]
    if not texts:
        return [], []

    req = EmbeddingRequest(texts=texts, input_type="document")
    emb_result = embedding_provider.embed(req)

    records: list[VectorRecord] = []
    embeddings: list[dict] = []

    for i, (chunk, vec) in enumerate(zip(chunks, emb_result.vectors)):
        chunk_id = _make_chunk_id(chunk["text"], chunk["source"], chunk["chunk_index"])
        doc_id = _make_doc_id(chunk["source"])
        records.append(
            VectorRecord(
                id=f"vec-{chunk_id}",
                document_id=doc_id,
                chunk_id=chunk_id,
                chunk_text=chunk["text"],
                vector=vec,
                metadata={
                    "source_file": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                    **chunk.get("metadata", {}),
                },
            )
        )
        embeddings.append(
            {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "vector": vec,
                "model": emb_result.model,
                "dimension": emb_result.dimension,
            }
        )

    return records, embeddings

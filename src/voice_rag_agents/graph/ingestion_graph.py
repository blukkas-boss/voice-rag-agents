"""IngestionGraph skeleton for LangGraph orchestration.

Implements the full ingestion pipeline with all nodes from the spec.
Uses mock providers from Wave 1 for embedding and vector store.
"""

from __future__ import annotations


from langgraph.graph import END, StateGraph
from voice_rag_agents.graph.states import VoiceRAGState
from voice_rag_agents.graph.conditional_logic import (
    dimension_mismatch_route,
    embedding_retry_route,
    ingestion_retry_route,
    parse_error_route,
)
from voice_rag_agents.model_clients.provider_factory import (
    get_embedding_provider,
    get_vector_store,
)
from voice_rag_agents.dataflows.vector_records import VectorRecord
from voice_rag_agents.dataflows.retrieval import chunk_to_vector_records
from voice_rag_agents.config.settings import get_settings


# ---------------------------------------------------------------------------
# Node factory functions (stubs that return state updates)
# ---------------------------------------------------------------------------


def discover_sources(state: VoiceRAGState) -> dict:
    """Discover source documents to ingest."""
    input_docs = state.get("input_documents", [])
    if input_docs:
        # Convert input documents to DocumentRecord format
        documents = []
        for i, doc_dict in enumerate(input_docs):
            doc = {
                "document_id": f"doc-{i+1}",
                "source_file": doc_dict.get("source_file", f"document_{i+1}"),
                "source_type": doc_dict.get("source_type", "markdown"),
                "title": doc_dict.get("title", ""),
                "text": doc_dict.get("text", ""),
                "metadata": doc_dict.get("metadata", {})
            }
            documents.append(doc)
        return {"documents": documents}
    return {}


def load_documents(state: VoiceRAGState) -> dict:
    """Load documents from source."""
    # For the skeleton, we'll assume documents are already loaded
    # In reality, this would read files from disk
    documents = state.get("documents", [])
    if documents:
        # Add loaded flag or content if needed
        return {"documents": documents}
    return {}


def parse_documents(state: VoiceRAGState) -> dict:
    """Parse documents into structured format."""
    documents = state.get("documents", [])
    if documents:
        # For the skeleton, we'll assume parsing succeeds
        # In reality, this would use parsers based on source_type
        parsed_docs = []
        for doc in documents:
            parsed_doc = doc.copy()
            # Add any parsing-specific fields
            parsed_doc["parsed"] = True
            parsed_docs.append(parsed_doc)
        return {"documents": parsed_docs}
    return {}


def normalize_documents(state: VoiceRAGState) -> dict:
    """Normalize document text and metadata."""
    documents = state.get("documents", [])
    if documents:
        # For the skeleton, we'll assume normalization succeeds
        normalized_docs = []
        for doc in documents:
            normalized_doc = doc.copy()
            # Normalize text: strip whitespace, etc.
            text = normalized_doc.get("text", "")
            normalized_doc["text"] = text.strip()
            normalized_docs.append(normalized_doc)
        return {"documents": normalized_docs}
    return {}


def chunk_documents(state: VoiceRAGState) -> dict:
    """Split documents into chunks."""
    documents = state.get("documents", [])
    if documents:
        # For the skeleton, we'll create simple chunks
        chunks = []
        chunk_id_counter = 1
        
        for doc in documents:
            text = doc.get("text", "")
            if text:
                # Simple chunking: split by paragraphs or fixed size
                # For skeleton, create one chunk per document
                chunk = {
                    "chunk_id": f"chunk-{chunk_id_counter}",
                    "document_id": doc.get("document_id", f"doc-{chunk_id_counter}"),
                    "sequence": 0,
                    "section": doc.get("section", ""),
                    "text": text[:500],  # Limit chunk size
                    "token_count": len(text.split()),  # Rough approximation
                    "metadata": doc.get("metadata", {})
                }
                chunks.append(chunk)
                chunk_id_counter += 1
        
        return {"chunks": chunks}
    return {}


def extract_metadata(state: VoiceRAGState) -> dict:
    """Extract and enrich metadata from chunks."""
    chunks = state.get("chunks", [])
    if chunks:
        # For the skeleton, we'll just pass through
        # In reality, this might extract entities, dates, etc.
        return {"chunks": chunks}
    return {}


def embed_chunks(state: VoiceRAGState) -> dict:
    """Embed chunks using embedding provider."""
    chunks = state.get("chunks", [])
    if not chunks or not any(c.get("text", "") for c in chunks):
        return {}
    embedding_provider = get_embedding_provider()
    _, embedding_records = chunk_to_vector_records(chunks, embedding_provider)
    # NOTE: prepare_vector_records is the SOLE writer of `vector_records` to
    # avoid two nodes writing the same state key in one run (langgraph drops
    # conflicting concurrent writes without a reducer).
    if embedding_records:
        return {"embeddings": embedding_records}
    return {}


def validate_embeddings(state: VoiceRAGState) -> dict:
    """Validate embeddings dimension and quality."""
    embeddings = state.get("embeddings", [])
    expected_dim = 2048  # From config
    
    if embeddings:
        # Check dimensions
        invalid_embeddings = []
        for i, emb in enumerate(embeddings):
            vector = emb.get("vector", [])
            if len(vector) != expected_dim:
                invalid_embeddings.append(i)
        
        if invalid_embeddings:
            # Return error for dimension mismatch
            error = {
                "code": "EMBEDDING_DIMENSION_MISMATCH",
                "message": f"Embedding dimension mismatch: expected {expected_dim}, got {len(embeddings[0].get('vector', [])) if embeddings else 0}",
                "node": "validate_embeddings",
                "details": {"expected": expected_dim, "actual": len(embeddings[0].get('vector', [])) if embeddings else 0}
            }
            return {"errors": [state.get("errors", []) + [error]] if state.get("errors") else [error]}
    
    return {}


def prepare_vector_records(state: VoiceRAGState) -> dict:
    """Prepare chunks + embeddings for vector store upsert."""
    chunks = state.get("chunks", [])
    embeddings = state.get("embeddings", [])
    
    if chunks and embeddings and len(chunks) == len(embeddings):
        vector_records = []
        for chunk, emb in zip(chunks, embeddings):
            vector_record = VectorRecord(
                id=f"vec-{chunk.get('chunk_id', 'unknown')}",
                document_id=chunk.get("document_id", ""),
                chunk_id=chunk.get("chunk_id", ""),
                chunk_text=chunk.get("text", ""),
                vector=emb.get("vector", []),
                metadata=chunk.get("metadata", {})
            )
            vector_records.append(vector_record)
        
        # Convert to dicts for state storage
        return {"vector_records": [vr.model_dump() for vr in vector_records]}
    return {}


def _rebuild_vector_records(state: VoiceRAGState) -> list[VectorRecord]:
    """Get vector records from state, rebuilding from chunks+embeddings if the
    `vector_records` key isn't populated in this node's state view.

    Defensive: langgraph state-merge timing across the ingestion pipeline can
    leave a node without an upstream key; rebuilding keeps upsert correct.
    """
    raw = state.get("vector_records", [])
    if raw:
        return [VectorRecord(**vr) for vr in raw]
    chunks = state.get("chunks", [])
    embeddings = state.get("embeddings", [])
    records: list[VectorRecord] = []
    for chunk, emb in zip(chunks, embeddings):
        records.append(
            VectorRecord(
                id=f"vec-{chunk.get('chunk_id', 'unknown')}",
                document_id=chunk.get("document_id", ""),
                chunk_id=chunk.get("chunk_id", ""),
                chunk_text=chunk.get("text", ""),
                vector=emb.get("vector", []),
                metadata=chunk.get("metadata", {}),
            )
        )
    return records


def ensure_collection(state: VoiceRAGState) -> dict:
    """Ensure vector collection exists with correct dimension."""
    records = _rebuild_vector_records(state)
    if not records:
        return {}
    dimension = len(records[0].vector) if records[0].vector else 2048
    collection_name = get_settings().collection
    get_vector_store().ensure_collection(collection_name, dimension)
    # Don't return undeclared state keys (langgraph drops them). upsert_records
    # re-derives the collection name from settings.
    return {}


def upsert_records(state: VoiceRAGState) -> dict:
    """Upsert vector records to vector store."""
    records = _rebuild_vector_records(state)
    if not records:
        return {}
    store = get_vector_store()
    collection_name = state.get("collection_name") or get_settings().collection
    dimension = len(records[0].vector) if records[0].vector else 2048
    store.ensure_collection(collection_name, dimension)
    result = store.upsert(collection_name, records)
    # Persist the upsert count inside the declared `ingestion_report` channel.
    # Undeclared state keys are dropped by langgraph between supersteps, so we
    # must use a key present in VoiceRAGState.
    report = dict(state.get("ingestion_report", {}) or {})
    report["records_upserted"] = result.get("upserted", 0)
    report["vector_store_success"] = True
    return {"ingestion_report": report}


def verify_ingestion(state: VoiceRAGState) -> dict:
    """Verify that ingestion was successful (reads declared ingestion_report)."""
    report = dict(state.get("ingestion_report", {}) or {})
    report["ingestion_verified"] = report.get("records_upserted", 0) > 0
    return {"ingestion_report": report}


def write_ingestion_report(state: VoiceRAGState) -> dict:
    """Write ingestion report."""
    documents = state.get("documents", [])
    chunks = state.get("chunks", [])
    embeddings = state.get("embeddings", [])
    vector_records = state.get("vector_records", [])
    prior = dict(state.get("ingestion_report", {}) or {})
    records_upserted = prior.get("records_upserted", 0)

    report = {
        "run_id": state.get("run_id"),
        "timestamp": state.get("created_at"),
        "documents_processed": len(documents),
        "chunks_created": len(chunks),
        "embeddings_generated": len(embeddings),
        "vector_records_prepared": len(vector_records),
        "records_upserted": records_upserted,
        "ingestion_verified": prior.get("ingestion_verified", False),
        "status": "success" if records_upserted > 0 else "failed",
    }
    return {"ingestion_report": report}


def quarantine_document(state: VoiceRAGState) -> dict:
    """Route failed documents to quarantine."""
    documents = state.get("documents", [])
    if documents:
        # For the skeleton, we'll just mark them as quarantined
        quarantined_docs = []
        for doc in documents:
            quarantined_doc = doc.copy()
            quarantined_doc["quarantined"] = True
            quarantined_doc["quarantine_reason"] = "parse_error"
            quarantined_docs.append(quarantined_doc)
        
        return {"quarantined_documents": quarantined_docs}
    return {}


def handle_error(state: VoiceRAGState) -> dict:
    """Handle errors that occurred during processing."""
    errors = state.get("errors", [])
    if errors:
        # Return structured error response
        error_msg = errors[-1].get("message", "Unknown error") if isinstance(errors[-1], dict) else str(errors[-1])
        return {
            "ingestion_report": {
                "run_id": state.get("run_id"),
                "status": "failed",
                "error": error_msg
            },
            "errors": errors
        }
    return {"ingestion_report": {"status": "failed", "error": "Unknown error"}}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_ingestion_graph() -> StateGraph:
    """Build and compile the IngestionGraph StateGraph."""
    
    # Create the state graph
    workflow = StateGraph(VoiceRAGState)
    
    # Add all nodes
    workflow.add_node("discover_sources", discover_sources)
    workflow.add_node("load_documents", load_documents)
    workflow.add_node("parse_documents", parse_documents)
    workflow.add_node("normalize_documents", normalize_documents)
    workflow.add_node("chunk_documents", chunk_documents)
    workflow.add_node("extract_metadata", extract_metadata)
    workflow.add_node("embed_chunks", embed_chunks)
    workflow.add_node("validate_embeddings", validate_embeddings)
    workflow.add_node("prepare_vector_records", prepare_vector_records)
    workflow.add_node("ensure_collection", ensure_collection)
    workflow.add_node("upsert_records", upsert_records)
    workflow.add_node("verify_ingestion", verify_ingestion)
    workflow.add_node("write_ingestion_report", write_ingestion_report)
    workflow.add_node("quarantine_document", quarantine_document)
    workflow.add_node("handle_error", handle_error)
    workflow.add_node("retry_embed_chunks", embed_chunks)  # Reuse embed_chunks for retry
    workflow.add_node("retry_upsert", upsert_records)    # Reuse upsert_records for retry
    
    # Set entry point
    workflow.set_entry_point("discover_sources")
    
    # Add edges - linear flow first
    workflow.add_edge("discover_sources", "load_documents")
    workflow.add_edge("load_documents", "parse_documents")
    workflow.add_edge("parse_documents", "normalize_documents")
    workflow.add_edge("normalize_documents", "chunk_documents")
    workflow.add_edge("chunk_documents", "extract_metadata")
    workflow.add_edge("extract_metadata", "embed_chunks")
    # NOTE: embed_chunks -> validate_embeddings and validate_embeddings ->
    # prepare_vector_records are handled by the conditional edges below; adding
    # direct edges too would double-wire the path and drop state on fan-in.
    workflow.add_edge("prepare_vector_records", "ensure_collection")
    workflow.add_edge("ensure_collection", "upsert_records")
    workflow.add_edge("upsert_records", "verify_ingestion")
    workflow.add_edge("verify_ingestion", "write_ingestion_report")
    workflow.add_edge("write_ingestion_report", END)
    
    # Add conditional edges
    
    # Parse error -> quarantine or continue
    workflow.add_conditional_edges(
        "parse_documents",
        parse_error_route,
        {
            "quarantine": "quarantine_document",
            "normalize": "normalize_documents"
        }
    )
    
    # Quarantine document leads to end (for now)
    workflow.add_edge("quarantine_document", END)
    
    # Embedding validation -> check dimensions or retry
    workflow.add_conditional_edges(
        "validate_embeddings",
        dimension_mismatch_route,
        {
            "upsert": "prepare_vector_records",
            "error": "handle_error"
        }
    )
    
    # Embedding retry logic
    workflow.add_conditional_edges(
        "embed_chunks",
        embedding_retry_route,
        {
            "retry": "retry_embed_chunks",
            "validate": "validate_embeddings",
            "error": "handle_error"
        }
    )
    
    # Retry embedding leads back to validation
    workflow.add_edge("retry_embed_chunks", "validate_embeddings")
    
    # Upsert retry logic
    workflow.add_conditional_edges(
        "upsert_records",
        ingestion_retry_route,
        {
            "retry": "retry_upsert",
            "verify": "verify_ingestion",
            "error": "handle_error"
        }
    )
    
    # Retry upsert leads back to verification
    workflow.add_edge("retry_upsert", "verify_ingestion")
    
    # Handle error leads to end
    workflow.add_edge("handle_error", END)
    
    return workflow.compile()


# ---------------------------------------------------------------------------
# Convenience function for external use
# ---------------------------------------------------------------------------


def run_ingestion_graph(initial_state: VoiceRAGState) -> VoiceRAGState:
    """Run the ingestion graph with initial state and return final state."""
    graph = build_ingestion_graph()
    return graph.invoke(initial_state)


if __name__ == "__main__":
    # Simple test to verify the graph compiles
    graph = build_ingestion_graph()
    print("IngestionGraph built successfully!")
    
    # Test with a simple state
    test_state: VoiceRAGState = {
        "run_id": "test-run-1",
        "request_type": "ingest",
        "user_id": "test-user",
        "session_id": "test-session",
        "created_at": "2024-01-01T00:00:00Z",
        "runtime_profile": "mock",
        "input_documents": [
            {
                "source_file": "test.md",
                "source_type": "markdown",
                "title": "Test Document",
                "text": "This is a test document about API rates and third-party risks.",
                "metadata": {"project": "test"}
            }
        ]
    }
    
    try:
        result = run_ingestion_graph(test_state)
        report = result.get("ingestion_report", {})
        print(f"Test run completed. Status: {report.get('status', 'unknown')}")
        print(f"Documents processed: {report.get('documents_processed', 0)}")
        print(f"Chunks created: {report.get('chunks_created', 0)}")
        print(f"Records upserted: {report.get('records_upserted', 0)}")
    except Exception as e:
        print(f"Test run failed: {e}")
        import traceback
        traceback.print_exc()
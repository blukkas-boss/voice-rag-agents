"""QueryGraph skeleton for LangGraph orchestration.

Implements the full query processing pipeline with all nodes from the spec.
Uses mock providers from Wave 1 for STT, embedding, vector store, and LLM.
"""

from __future__ import annotations


from langgraph.graph import END, StateGraph
from voice_rag_agents.graph.states import VoiceRAGState
from voice_rag_agents.graph.conditional_logic import (
    citation_route,
    query_input_route,
    retrieval_route,
    stt_confidence_route,
)
from voice_rag_agents.dataflows.mock_vector_store import MockVectorStore
from voice_rag_agents.model_clients.stt_adapter import make_stt_provider
from voice_rag_agents.model_clients.embedding_adapter import OpenAIEmbeddingAdapter
from voice_rag_agents.model_clients.llm_adapter import OpenAIChatAdapter
from voice_rag_agents.dataflows.retrieval import assemble_context as _assemble_context
from voice_rag_agents.dataflows.vector_records import SearchResult
from voice_rag_agents.config.settings import get_settings


# ---------------------------------------------------------------------------
# Node factory functions (stubs that return state updates)
# ---------------------------------------------------------------------------


def accept_query(state: VoiceRAGState) -> dict:
    """Accept the query and initialize query processing."""
    return {}


def transcribe_voice(state: VoiceRAGState) -> dict:
    """Transcribe voice input to text using STT provider."""
    audio_path = state.get("input_audio_path")
    if not audio_path:
        return {}
    settings = get_settings()
    stt_provider = make_stt_provider(
        mode=settings.stt_provider,
        command=settings.stt_command.split() if settings.stt_command else None,
    )
    result = stt_provider.transcribe(audio_path)
    return {
        "transcript": result.transcript,
        "stt_confidence": result.confidence,
    }


def normalize_query(state: VoiceRAGState) -> dict:
    """Normalize the query text."""
    query = state.get("input_text") or state.get("transcript", "")
    # Simple normalization: lowercase and strip
    normalized = query.lower().strip()
    return {"normalized_query": normalized}


def rewrite_query(state: VoiceRAGState) -> dict:
    """Optional query rewrite for better retrieval."""
    # For the skeleton, we'll just pass through
    normalized = state.get("normalized_query", "")
    return {"rewritten_query": normalized}


def embed_query(state: VoiceRAGState) -> dict:
    """Embed the query using embedding provider."""
    query_to_embed = state.get("rewritten_query") or state.get("normalized_query", "")
    if not query_to_embed:
        return {}
    settings = get_settings()
    embedding_provider = OpenAIEmbeddingAdapter(
        base_url=settings.embedding_base_url,
        model=settings.embedding_model,
        api_key=settings.embedding_api_key,
        dimension=settings.embedding_dim,
    )
    from voice_rag_agents.model_clients.interfaces import EmbeddingRequest
    result = embedding_provider.embed(
        EmbeddingRequest(texts=[query_to_embed], input_type="query")
    )
    if result.vectors:
        return {"query_embedding": result.vectors[0]}
    return {}


def search_vector_store(state: VoiceRAGState) -> dict:
    """Search vector store for similar chunks."""
    query_vector = state.get("query_embedding")
    if not query_vector:
        return {}
    settings = get_settings()
    vector_store = MockVectorStore()  # Default; swap to MilvusAdapter in integration
    vector_store.ensure_collection(settings.collection, len(query_vector))
    from voice_rag_agents.dataflows.vector_records import SearchRequest
    request = SearchRequest(query_vector=query_vector, top_k=settings.top_k)
    results = vector_store.search(settings.collection, request)
    if results:
        return {"retrieval_results": [r.model_dump() for r in results]}
    return {}


def apply_metadata_filters(state: VoiceRAGState) -> dict:
    """Apply metadata filters to retrieval results."""
    # For the skeleton, we'll just pass through
    return {}


def rerank_results(state: VoiceRAGState) -> dict:
    """Optional reranking of results."""
    # For the skeleton, we'll just pass through
    return {}


def assemble_context(state: VoiceRAGState) -> dict:
    """Assemble context from retrieval results with citations."""
    raw = state.get("retrieval_results", [])
    results = [SearchResult(**r) if isinstance(r, dict) else r for r in raw]
    context, citations = _assemble_context(results)
    out: dict = {"assembled_context": context}
    if citations:
        out["citations"] = [c.model_dump() for c in citations]
    return out


def generate_answer(state: VoiceRAGState) -> dict:
    """Generate answer using LLM provider grounded in assembled context."""
    question = state.get("input_text") or state.get("transcript", "")
    context = state.get("assembled_context", "")
    if not question or not context:
        return {}
    settings = get_settings()
    llm_provider = OpenAIChatAdapter(
        base_url=settings.llm_base_url,
        model=settings.llm_model,
        api_key=settings.llm_api_key,
    )
    from voice_rag_agents.model_clients.interfaces import ChatMessage, ChatRequest
    request = ChatRequest(
        messages=[
            ChatMessage(role="system", content="Answer ONLY using the provided context. Cite sources as [S1], [S2], etc."),
            ChatMessage(role="user", content=f"Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    result = llm_provider.chat(request)
    return {"answer": result.content}


def validate_citations(state: VoiceRAGState) -> dict:
    """Validate that answer citations map to retrieved chunks."""
    # For the skeleton, we'll simulate validation
    answer = state.get("answer", "")
    citations = state.get("citations", [])
    
    # Simple validation: check if answer has citation markers
    if "[S" in answer and answer.count("[S") == len(citations):
        # Valid citations
        return {}
    else:
        # Invalid or missing citations - add error for retry logic
        error = {
            "code": "CITATION_VALIDATION_FAILED",
            "message": "Answer citations do not match retrieved chunks",
            "node": "validate_citations"
        }
        return {"errors": [state.get("errors", []) + [error]] if state.get("errors") else [error]}


def validate_groundedness(state: VoiceRAGState) -> dict:
    """Validate that answer is grounded in retrieved context."""
    # For the skeleton, we'll assume it's grounded if we have citations
    answer = state.get("answer", "")
    citations = state.get("citations", [])
    
    if answer and citations:
        return {}
    else:
        error = {
            "code": "GROUNDEDNESS_VALIDATION_FAILED",
            "message": "Answer lacks sufficient grounding in retrieved context",
            "node": "validate_groundedness"
        }
        return {"errors": [state.get("errors", []) + [error]] if state.get("errors") else [error]}


def format_response(state: VoiceRAGState) -> dict:
    """Format the final response."""
    answer = state.get("answer", "I do not have enough evidence in the knowledge base to answer that.")
    return {"answer": answer}


def no_evidence_response(state: VoiceRAGState) -> dict:
    """Return a no-evidence response."""
    return {
        "answer": "I do not have enough evidence in the knowledge base to answer that."
    }


def handle_error(state: VoiceRAGState) -> dict:
    """Handle errors that occurred during processing."""
    errors = state.get("errors", [])
    if errors:
        # Return structured error response
        error_msg = errors[-1].get("message", "Unknown error") if isinstance(errors[-1], dict) else str(errors[-1])
        return {
            "answer": f"I encountered an error while processing your request: {error_msg}",
            "errors": errors
        }
    return {"answer": "I encountered an error while processing your request."}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_query_graph() -> StateGraph:
    """Build and compile the QueryGraph StateGraph."""
    
    # Create the state graph
    workflow = StateGraph(VoiceRAGState)
    
    # Add all nodes
    workflow.add_node("accept_query", accept_query)
    workflow.add_node("transcribe_voice", transcribe_voice)
    workflow.add_node("normalize_query", normalize_query)
    workflow.add_node("rewrite_query", rewrite_query)
    workflow.add_node("embed_query", embed_query)
    workflow.add_node("search_vector_store", search_vector_store)
    workflow.add_node("apply_metadata_filters", apply_metadata_filters)
    workflow.add_node("rerank_results", rerank_results)
    workflow.add_node("assemble_context", assemble_context)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("validate_citations", validate_citations)
    workflow.add_node("validate_groundedness", validate_groundedness)
    workflow.add_node("format_response", format_response)
    workflow.add_node("no_evidence_response", no_evidence_response)
    workflow.add_node("handle_error", handle_error)
    
    # Set entry point
    workflow.set_entry_point("accept_query")
    
    # Add edges - linear flow first
    workflow.add_edge("accept_query", "transcribe_voice")
    workflow.add_edge("transcribe_voice", "normalize_query")
    workflow.add_edge("normalize_query", "rewrite_query")
    workflow.add_edge("rewrite_query", "embed_query")
    workflow.add_edge("embed_query", "search_vector_store")
    workflow.add_edge("search_vector_store", "apply_metadata_filters")
    workflow.add_edge("apply_metadata_filters", "rerank_results")
    workflow.add_edge("rerank_results", "assemble_context")
    workflow.add_edge("assemble_context", "generate_answer")
    workflow.add_edge("generate_answer", "validate_citations")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_citations",
        citation_route,
        {
            "valid": "validate_groundedness",
            "retry": "generate_answer",  # Retry answer generation
            "invalid": "no_evidence_response"
        }
    )
    
    workflow.add_conditional_edges(
        "validate_groundedness",
        lambda x: "format_response" if not x.get("errors") else "handle_error",
        {
            "format_response": "format_response",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_edge("format_response", END)
    workflow.add_edge("no_evidence_response", END)
    workflow.add_edge("handle_error", END)
    
    # Add STT confidence routing after transcribe_voice
    workflow.add_conditional_edges(
        "transcribe_voice",
        stt_confidence_route,
        {
            "acceptable": "normalize_query",
            "low": "no_evidence_response"  # Ask for clarification in real implementation
        }
    )
    
    # Add retrieval routing after search_vector_store
    workflow.add_conditional_edges(
        "search_vector_store",
        retrieval_route,
        {
            "has_results": "apply_metadata_filters",
            "no_results": "no_evidence_response",
            "error": "handle_error"
        }
    )
    
    # Add query input routing after accept_query
    workflow.add_conditional_edges(
        "accept_query",
        query_input_route,
        {
            "voice": "transcribe_voice",
            "text": "normalize_query",  # Skip transcription for text input
            "error": "handle_error"
        }
    )
    
    return workflow.compile()


# ---------------------------------------------------------------------------
# Convenience function for external use
# ---------------------------------------------------------------------------


def run_query_graph(initial_state: VoiceRAGState) -> VoiceRAGState:
    """Run the query graph with initial state and return final state."""
    graph = build_query_graph()
    return graph.invoke(initial_state)


if __name__ == "__main__":
    # Simple test to verify the graph compiles
    graph = build_query_graph()
    print("QueryGraph built successfully!")
    
    # Test with a simple state
    test_state: VoiceRAGState = {
        "run_id": "test-run-1",
        "request_type": "query",
        "user_id": "test-user",
        "session_id": "test-session",
        "created_at": "2024-01-01T00:00:00Z",
        "runtime_profile": "mock",
        "input_text": "What are the risks?",
    }
    
    try:
        result = run_query_graph(test_state)
        print(f"Test run completed. Answer: {result.get('answer', 'No answer')}")
    except Exception as e:
        print(f"Test run failed: {e}")
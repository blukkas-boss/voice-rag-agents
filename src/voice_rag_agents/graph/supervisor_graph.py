"""SupervisorGraph for LangGraph orchestration.

Routes requests to the appropriate subgraph (ingestion, query, admin, evaluation).
"""

from __future__ import annotations


from langgraph.graph import END, StateGraph
from voice_rag_agents.graph.states import VoiceRAGState
from voice_rag_agents.graph.conditional_logic import route_request_type


# ---------------------------------------------------------------------------
# Node factory functions
# ---------------------------------------------------------------------------


def initialize_run(state: VoiceRAGState) -> dict:
    """Initialize a new run with basic metadata."""
    # Ensure run_id exists
    if not state.get("run_id"):
        import uuid
        from datetime import datetime, timezone
        state["run_id"] = str(uuid.uuid4())
        state["created_at"] = datetime.now(timezone.utc).isoformat()
    
    # Initialize tracking fields if not present
    updates = {}
    if "errors" not in state:
        updates["errors"] = []
    if "warnings" not in state:
        updates["warnings"] = []
    if "retries" not in state:
        updates["retries"] = {}
    if "human_actions_required" not in state:
        updates["human_actions_required"] = []
    
    return updates


def classify_request(state: VoiceRAGState) -> dict:
    """Classify the request type if not already set."""
    # If request_type is already set, just pass through
    if state.get("request_type"):
        return {}
    
    # Otherwise, try to classify based on inputs
    if state.get("input_documents"):
        return {"request_type": "ingest"}
    elif state.get("input_text") or state.get("input_audio_path"):
        return {"request_type": "query"}
    elif state.get("command"):
        cmd = state["command"].lower()
        if cmd in ["health", "reindex", "backup", "migrate"]:
            return {"request_type": "admin"}
        elif cmd == "eval":
            return {"request_type": "eval"}
    
    # Default to query if we have some input, otherwise error
    if state.get("input_text") or state.get("input_audio_path"):
        return {"request_type": "query"}
    else:
        return {"request_type": "unknown"}


def route_to_subgraph(state: VoiceRAGState) -> dict:
    """Route to the appropriate subgraph based on request_type.
    
    This node doesn't modify state - it just determines the next step via conditional edges.
    """
    return {}


def summarize_subgraph_result(state: VoiceRAGState) -> dict:
    """Summarize the result from subgraph execution."""
    # Extract key information from state for final response
    request_type = state.get("request_type", "unknown")
    final_status = state.get("final_status", "unknown")
    errors = state.get("errors", [])
    
    # Create a summary
    summary = {
        "run_id": state.get("run_id"),
        "request_type": request_type,
        "status": final_status,
        "message": f"Completed {request_type} request with status {final_status}"
    }
    
    if errors:
        summary["errors"] = [e.get("message", str(e)) if isinstance(e, dict) else str(e) for e in errors]
    
    # Add specific summaries based on request type
    if request_type == "ingest":
        report = state.get("ingestion_report", {})
        summary.update({
            "documents_processed": report.get("documents_processed", 0),
            "chunks_created": report.get("chunks_created", 0),
            "records_upserted": report.get("records_upserted", 0)
        })
    elif request_type == "query":
        summary.update({
            "answer": state.get("answer", ""),
            "has_citations": bool(state.get("citations"))
        })
    
    return {"run_summary": summary}


def handle_error(state: VoiceRAGState) -> dict:
    """Handle errors that occurred during processing."""
    errors = state.get("errors", [])
    if errors:
        # Format error message
        error_msg = errors[-1].get("message", "Unknown error") if isinstance(errors[-1], dict) else str(errors[-1])
        
        summary = {
            "run_id": state.get("run_id"),
            "request_type": state.get("request_type", "unknown"),
            "status": "failed",
            "message": f"Failed to process request: {error_msg}",
            "error": error_msg
        }
        
        return {
            "run_summary": summary,
            "final_status": "failed",
            "answer": f"I encountered an error while processing your request: {error_msg}"
        }
    
    # Generic error handler
    return {
        "run_summary": {
            "run_id": state.get("run_id"),
            "request_type": state.get("request_type", "unknown"),
            "status": "failed",
            "message": "An unknown error occurred"
        },
        "final_status": "failed",
        "answer": "I encountered an error while processing your request."
    }


# ---------------------------------------------------------------------------
# Subgraph wrapper functions
# ---------------------------------------------------------------------------


def run_ingestion_subgraph(state: VoiceRAGState) -> dict:
    """Wrapper to run ingestion subgraph."""
    try:
        from .ingestion_graph import run_ingestion_graph
        result_state = run_ingestion_graph(state)
        # Extract key results to merge back into state
        return {
            "documents": result_state.get("documents", []),
            "chunks": result_state.get("chunks", []),
            "embeddings": result_state.get("embeddings", []),
            "vector_records": result_state.get("vector_records", []),
            "ingestion_report": result_state.get("ingestion_report", {}),
            "errors": result_state.get("errors", state.get("errors", [])),
            "final_status": "success" if result_state.get("ingestion_report", {}).get("status") == "success" else "partial"
        }
    except Exception as e:
        return {
            "errors": state.get("errors", []) + [{
                "code": "INGESTION_SUBGRAPH_ERROR",
                "message": str(e),
                "node": "run_ingestion_subgraph"
            }],
            "final_status": "failed"
        }


def run_query_subgraph(state: VoiceRAGState) -> dict:
    """Wrapper to run query subgraph."""
    try:
        from .query_graph import run_query_graph
        result_state = run_query_graph(state)
        # Extract key results to merge back into state
        return {
            "transcript": result_state.get("transcript"),
            "stt_confidence": result_state.get("stt_confidence"),
            "normalized_query": result_state.get("normalized_query"),
            "rewritten_query": result_state.get("rewritten_query"),
            "query_embedding": result_state.get("query_embedding"),
            "retrieval_results": result_state.get("retrieval_results", []),
            "assembled_context": result_state.get("assembled_context", ""),
            "answer": result_state.get("answer", ""),
            "citations": result_state.get("citations", []),
            "answer_quality": result_state.get("answer_quality", {}),
            "errors": result_state.get("errors", state.get("errors", [])),
            "final_status": "success" if not result_state.get("errors") else "partial"
        }
    except Exception as e:
        return {
            "errors": state.get("errors", []) + [{
                "code": "QUERY_SUBGRAPH_ERROR",
                "message": str(e),
                "node": "run_query_subgraph"
            }],
            "final_status": "failed"
        }


def run_admin_subgraph(state: VoiceRAGState) -> dict:
    """Wrapper for admin subgraph (stub for skeleton)."""
    # For the skeleton, we'll return a basic admin response
    command = state.get("command", "").lower()
    
    if command == "health":
        return {
            "answer": "System is healthy (mock mode)",
            "final_status": "success"
        }
    elif command in ["reindex", "backup", "migrate"]:
        return {
            "answer": f"Admin command '{command}' completed (mock mode)",
            "final_status": "success"
        }
    else:
        return {
            "answer": f"Unknown admin command: {command}",
            "final_status": "failed"
        }


def run_evaluation_subgraph(state: VoiceRAGState) -> dict:
    """Wrapper for evaluation subgraph (stub for skeleton)."""
    return {
        "answer": "Evaluation completed (mock mode)",
        "final_status": "success"
    }


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_supervisor_graph() -> StateGraph:
    """Build and compile the SupervisorGraph StateGraph."""
    
    # Create the state graph
    workflow = StateGraph(VoiceRAGState)
    
    # Add all nodes
    workflow.add_node("initialize_run", initialize_run)
    workflow.add_node("classify_request", classify_request)
    workflow.add_node("route_to_subgraph", route_to_subgraph)
    workflow.add_node("run_ingestion_subgraph", run_ingestion_subgraph)
    workflow.add_node("run_query_subgraph", run_query_subgraph)
    workflow.add_node("run_admin_subgraph", run_admin_subgraph)
    workflow.add_node("run_evaluation_subgraph", run_evaluation_subgraph)
    workflow.add_node("summarize_subgraph_result", summarize_subgraph_result)
    workflow.add_node("handle_error", handle_error)
    
    # Set entry point
    workflow.set_entry_point("initialize_run")
    
    # Add edges
    workflow.add_edge("initialize_run", "classify_request")
    workflow.add_edge("classify_request", "route_to_subgraph")
    
    # Add conditional routing based on request_type
    workflow.add_conditional_edges(
        "route_to_subgraph",
        route_request_type,
        {
            "ingestion_subgraph": "run_ingestion_subgraph",
            "query_subgraph": "run_query_subgraph",
            "admin_subgraph": "run_admin_subgraph",
            "evaluation_subgraph": "run_evaluation_subgraph",
            "handle_error": "handle_error",
            "__end__": END
        }
    )
    
    # All subgraphs lead to summarization
    workflow.add_edge("run_ingestion_subgraph", "summarize_subgraph_result")
    workflow.add_edge("run_query_subgraph", "summarize_subgraph_result")
    workflow.add_edge("run_admin_subgraph", "summarize_subgraph_result")
    workflow.add_edge("run_evaluation_subgraph", "summarize_subgraph_result")
    
    # Summarization leads to end
    workflow.add_edge("summarize_subgraph_result", END)
    
    # Error handling
    workflow.add_edge("handle_error", END)
    
    return workflow.compile()


# ---------------------------------------------------------------------------
# Convenience function for external use
# ---------------------------------------------------------------------------


def run_supervisor_graph(initial_state: VoiceRAGState) -> VoiceRAGState:
    """Run the supervisor graph with initial state and return final state."""
    graph = build_supervisor_graph()
    return graph.invoke(initial_state)


if __name__ == "__main__":
    # Simple test to verify the graph compiles
    graph = build_supervisor_graph()
    print("SupervisorGraph built successfully!")
    
    # Test with a simple query state
    test_state: VoiceRAGState = {
        "request_type": "query",
        "user_id": "test-user",
        "session_id": "test-session",
        "runtime_profile": "mock",
        "input_text": "What are the risks?",
    }
    
    try:
        result = run_supervisor_graph(test_state)
        summary = result.get("run_summary", {})
        print("Test run completed.")
        print(f"Request type: {summary.get('request_type')}")
        print(f"Status: {summary.get('status')}")
        print(f"Message: {summary.get('message')}")
        print(f"Answer: {result.get('answer', 'No answer')}")
    except Exception as e:
        print(f"Test run failed: {e}")
        import traceback
        traceback.print_exc()
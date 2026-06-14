"""Run artifact store for LangGraph observability.

Records node execution events with timestamps for debugging and monitoring.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from voice_rag_agents.graph.states import VoiceRAGState


class RunArtifactStore:
    """Append-only JSONL file per run_id, records node execution events.
    
    Events recorded:
    - run_started
    - node_started
    - node_completed
    - node_failed
    - provider_call_started
    - provider_call_completed
    - retrieval_completed
    - answer_generated
    - citation_validation_failed
    - run_completed
    """

    def __init__(self, artifact_dir: str = "./artifacts"):
        """Initialize the artifact store.
        
        Args:
            artifact_dir: Directory to store artifact files
        """
        self.artifact_dir = artifact_dir
        os.makedirs(self.artifact_dir, exist_ok=True)

    def _get_artifact_path(self, run_id: str) -> str:
        """Get the file path for a run_id artifact."""
        return os.path.join(self.artifact_dir, f"{run_id}.jsonl")

    def _write_event(self, run_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Write an event to the JSONL file.
        
        Args:
            run_id: Unique identifier for the run
            event_type: Type of event being recorded
            data: Event-specific data
        """
        if not run_id:
            raise ValueError("run_id is required for artifact recording")
        
        artifact_path = self._get_artifact_path(run_id)
        
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "event_type": event_type,
            "data": data
        }
        
        with open(artifact_path, 'a') as f:
            f.write(json.dumps(event) + '\n')

    # -----------------------------------------------------------------------
    # Event recording methods
    # -----------------------------------------------------------------------
    
    def record_run_started(self, run_id: str, initial_state: VoiceRAGState) -> None:
        """Record run started event."""
        self._write_event(run_id, "run_started", {
            "initial_state_keys": list(initial_state.keys()),
            "request_type": initial_state.get("request_type"),
            "user_id": initial_state.get("user_id")
        })

    def record_node_started(self, run_id: str, node_name: str, state: VoiceRAGState) -> None:
        """Record node started event."""
        self._write_event(run_id, "node_started", {
            "node_name": node_name,
            "state_keys": list(state.keys()),
            "has_errors": bool(state.get("errors"))
        })

    def record_node_completed(self, run_id: str, node_name: str, state: VoiceRAGState, 
                            execution_time_ms: Optional[float] = None) -> None:
        """Record node completed event."""
        self._write_event(run_id, "node_completed", {
            "node_name": node_name,
            "state_keys": list(state.keys()),
            "has_errors": bool(state.get("errors")),
            "execution_time_ms": execution_time_ms
        })

    def record_node_failed(self, run_id: str, node_name: str, error: Dict[str, Any], 
                          state: VoiceRAGState) -> None:
        """Record node failed event."""
        self._write_event(run_id, "node_failed", {
            "node_name": node_name,
            "error": error,
            "state_keys": list(state.keys()),
            "has_errors": bool(state.get("errors"))
        })

    def record_provider_call_started(self, run_id: str, provider_type: str, 
                                   provider_name: str, operation: str) -> None:
        """Record provider call started event."""
        self._write_event(run_id, "provider_call_started", {
            "provider_type": provider_type,  # stt, embedding, llm, vector_store
            "provider_name": provider_name,
            "operation": operation
        })

    def record_provider_call_completed(self, run_id: str, provider_type: str, 
                                     provider_name: str, operation: str,
                                     success: bool, execution_time_ms: Optional[float] = None,
                                     result_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record provider call completed event."""
        self._write_event(run_id, "provider_call_completed", {
            "provider_type": provider_type,
            "provider_name": provider_name,
            "operation": operation,
            "success": success,
            "execution_time_ms": execution_time_ms,
            "result_metadata": result_metadata or {}
        })

    def record_retrieval_completed(self, run_id: str, query: str, 
                                 results_count: int, execution_time_ms: Optional[float] = None) -> None:
        """Record retrieval completed event."""
        self._write_event(run_id, "retrieval_completed", {
            "query": query,
            "results_count": results_count,
            "execution_time_ms": execution_time_ms
        })

    def record_answer_generated(self, run_id: str, answer: str, 
                              citations_count: int, execution_time_ms: Optional[float] = None) -> None:
        """Record answer generated event."""
        self._write_event(run_id, "answer_generated", {
            "answer_length": len(answer),
            "citations_count": citations_count,
            "execution_time_ms": execution_time_ms
        })

    def record_citation_validation_failed(self, run_id: str, answer: str, 
                                        missing_citations: List[str]) -> None:
        """Record citation validation failed event."""
        self._write_event(run_id, "citation_validation_failed", {
            "answer": answer,
            "answer_length": len(answer),
            "missing_citations": missing_citations,
            "missing_count": len(missing_citations)
        })

    def record_run_completed(self, run_id: str, final_state: VoiceRAGState, 
                           execution_time_ms: Optional[float] = None) -> None:
        """Record run completed event."""
        self._write_event(run_id, "run_completed", {
            "final_status": final_state.get("final_status"),
            "has_errors": bool(final_state.get("errors")),
            "warnings_count": len(final_state.get("warnings", [])),
            "execution_time_ms": execution_time_ms
        })

    # -----------------------------------------------------------------------
    # Query methods
    # -----------------------------------------------------------------------
    
    def get_run_events(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all events for a run.
        
        Args:
            run_id: Unique identifier for the run
            
        Returns:
            List of event dictionaries, ordered by timestamp
        """
        if not run_id:
            return []
            
        artifact_path = self._get_artifact_path(run_id)
        
        if not os.path.exists(artifact_path):
            return []
        
        events = []
        try:
            with open(artifact_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
        except IOError:
            return []
        
        # Sort by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""))
        return events

    def get_latest_run(self) -> Optional[str]:
        """Get the most recent run_id based on file modification time.
        
        Returns:
            Most recent run_id, or None if no artifacts exist
        """
        if not os.path.exists(self.artifact_dir):
            return None
        
        artifact_files = [f for f in os.listdir(self.artifact_dir) 
                         if f.endswith('.jsonl')]
        
        if not artifact_files:
            return None
        
        # Sort by modification time, newest first
        artifact_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(self.artifact_dir, x)),
            reverse=True
        )
        
        return artifact_files[0][:-6] if artifact_files else None  # Remove .jsonl


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def get_artifact_store(artifact_dir: str = "./artifacts") -> RunArtifactStore:
    """Get a RunArtifactStore instance.
    
    Args:
        artifact_dir: Directory to store artifact files
        
    Returns:
        RunArtifactStore instance
    """
    return RunArtifactStore(artifact_dir)


if __name__ == "__main__":
    # Simple test
    import tempfile
    import shutil
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp()
    try:
        artifact_store = get_artifact_store(os.path.join(test_dir, "artifacts"))
        
        test_run_id = "test-run-123"
        test_state: VoiceRAGState = {
            "run_id": test_run_id,
            "request_type": "query",
            "user_id": "test-user",
            "input_text": "What is the answer?",
            "answer": "This is a test answer."
        }
        
        # Test recording events
        artifact_store.record_run_started(test_run_id, test_state)
        artifact_store.record_node_started(test_run_id, "accept_query", test_state)
        artifact_store.record_node_completed(test_run_id, "accept_query", test_state, 10.5)
        artifact_store.record_provider_call_started(test_run_id, "llm", "mock-llm", "chat")
        artifact_store.record_provider_call_completed(test_run_id, "llm", "mock-llm", "chat", True, 50.0)
        artifact_store.record_answer_generated(test_run_id, "This is a test answer.", 1, 30.0)
        artifact_store.record_run_completed(test_run_id, test_state, 100.0)
        
        # Test retrieving events
        events = artifact_store.get_run_events(test_run_id)
        print(f"Recorded {len(events)} events:")
        for event in events:
            print(f"  {event['event_type']} at {event['timestamp']}")
        
        # Test latest run
        latest = artifact_store.get_latest_run()
        print(f"Latest run: {latest}")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir)
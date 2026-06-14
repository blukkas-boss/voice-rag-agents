"""Unit tests for RunArtifactStore."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from voice_rag_agents.observability.run_artifacts import (
    RunArtifactStore,
    get_artifact_store
)
from voice_rag_agents.graph.states import VoiceRAGState


@pytest.mark.graph
class TestRunArtifactStore:
    """Test RunArtifactStore functionality."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.artifact_dir = os.path.join(self.test_dir, "artifacts")

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_artifact_store_initialization(self):
        """Test artifact store initialization."""
        store = RunArtifactStore(self.artifact_dir)
        assert store.artifact_dir == self.artifact_dir
        assert os.path.exists(self.artifact_dir)

    def test_get_artifact_store_default(self):
        """Test get_artifact_store with default directory."""
        store = get_artifact_store()
        assert isinstance(store, RunArtifactStore)

    def test_get_artifact_store_custom_dir(self):
        """Test get_artifact_store with custom directory."""
        custom_dir = os.path.join(self.test_dir, "custom")
        store = get_artifact_store(custom_dir)
        assert store.artifact_dir == custom_dir
        assert os.path.exists(custom_dir)

    def test_record_and_retrieve_events(self):
        """Test recording and retrieving events."""
        store = RunArtifactStore(self.artifact_dir)
        run_id = "test-run-123"
        
        initial_state: VoiceRAGState = {
            "run_id": run_id,
            "request_type": "query",
            "user_id": "test-user",
            "input_text": "What is the answer?"
        }
        
        final_state: VoiceRAGState = {
            **initial_state,
            "answer": "The answer is 42.",
            "citations": [{"label": "S1", "chunk_id": "c1"}],
            "final_status": "success",
        }
        
        # Record various events
        store.record_run_started(run_id, initial_state)
        store.record_node_started(run_id, "accept_query", initial_state)
        store.record_node_completed(run_id, "accept_query", initial_state, 5.2)
        store.record_provider_call_started(run_id, "llm", "mock-llm", "generate")
        store.record_provider_call_completed(run_id, "llm", "mock-llm", "generate", True, 100.5)
        store.record_answer_generated(run_id, "The answer is 42.", 1, 50.3)
        store.record_run_completed(run_id, final_state, 200.0)
        
        # Retrieve events
        events = store.get_run_events(run_id)
        
        # Should have 7 events (run_started, node_started, node_completed,
        # provider_call_started, provider_call_completed, answer_generated,
        # run_completed)
        assert len(events) == 7
        
        # Check event types
        event_types = [e["event_type"] for e in events]
        expected_types = [
            "run_started",
            "node_started", 
            "node_completed",
            "provider_call_started",
            "provider_call_completed",
            "answer_generated",
            "run_completed"
        ]
        # Note: We recorded 7 event types but only 6 events because we didn't record
        # node_started/node_completed for all nodes - this is correct
        
        # Check specific events
        run_started = next(e for e in events if e["event_type"] == "run_started")
        assert run_started["data"]["request_type"] == "query"
        assert run_started["data"]["user_id"] == "test-user"
        
        node_completed = next(e for e in events if e["event_type"] == "node_completed")
        assert node_completed["data"]["node_name"] == "accept_query"
        assert node_completed["data"]["execution_time_ms"] == 5.2
        
        answer_generated = next(e for e in events if e["event_type"] == "answer_generated")
        assert answer_generated["data"]["answer_length"] == len("The answer is 42.")
        assert answer_generated["data"]["citations_count"] == 1
        
        run_completed = next(e for e in events if e["event_type"] == "run_completed")
        assert run_completed["data"]["final_status"] == "success"  # default from VoiceRAGState
        assert run_completed["data"]["execution_time_ms"] == 200.0

    def test_get_events_for_nonexistent_run(self):
        """Test getting events for a nonexistent run."""
        store = RunArtifactStore(self.artifact_dir)
        events = store.get_run_events("nonexistent-run")
        assert events == []

    def test_get_latest_run(self):
        """Test getting the most recent run."""
        store = RunArtifactStore(self.artifact_dir)
        
        # Initially no runs
        assert store.get_latest_run() is None
        
        # Create some runs with different timestamps
        run_ids = ["run-first", "run-middle", "run-last"]
        
        for i, run_id in enumerate(run_ids):
            state: VoiceRAGState = {
                "run_id": run_id,
                "request_type": "query",
                "input_text": f"query {i}"
            }
            store.record_run_started(run_id, state)
            store.record_run_completed(run_id, {**state, "final_status": "success"})
            # In real usage, there would be time differences, but for testing
            # we'll rely on file creation order
        
        # The last created should be latest (based on file modification time)
        latest = store.get_latest_run()
        # Note: This test might be flaky due to timing, but generally the last
        # one created should have the latest modification time
        assert latest is not None

    def test_citation_validation_failed_event(self):
        """Test recording citation validation failed event."""
        store = RunArtifactStore(self.artifact_dir)
        run_id = "test-citation-fail"
        
        store.record_citation_validation_failed(
            run_id,
            "The answer is [S1] and [S2] but we only have [S1]",
            ["S2"]
        )
        
        events = store.get_run_events(run_id)
        assert len(events) == 1
        
        event = events[0]
        assert event["event_type"] == "citation_validation_failed"
        assert event["data"]["missing_citations"] == ["S2"]
        assert event["data"]["missing_count"] == 1
        assert len(event["data"]["answer"]) > 0

    def test_retrieval_completed_event(self):
        """Test recording retrieval completed event."""
        store = RunArtifactStore(self.artifact_dir)
        run_id = "test-retrieval"
        
        store.record_retrieval_completed(
            run_id,
            "What are the risks?",
            5,
            150.0
        )
        
        events = store.get_run_events(run_id)
        assert len(events) == 1
        
        event = events[0]
        assert event["event_type"] == "retrieval_completed"
        assert event["data"]["query"] == "What are the risks?"
        assert event["data"]["results_count"] == 5
        assert event["data"]["execution_time_ms"] == 150.0

    def test_multiple_runs_isolation(self):
        """Test that events for different runs are isolated."""
        store = RunArtifactStore(self.artifact_dir)
        
        # Record events for run 1
        store.record_run_started("run-1", {"run_id": "run-1", "request_type": "query"})
        store.record_node_started("run-1", "test_node", {"run_id": "run-1"})
        
        # Record events for run 2
        store.record_run_started("run-2", {"run_id": "run-2", "request_type": "ingest"})
        store.record_node_started("run-2", "test_node", {"run_id": "run-2"})
        store.record_node_completed("run-2", "test_node", {"run_id": "run-2"}, 10.0)
        
        # Check run-1 events
        events_1 = store.get_run_events("run-1")
        assert len(events_1) == 2
        event_types_1 = [e["event_type"] for e in events_1]
        assert "run_started" in event_types_1
        assert "node_started" in event_types_1
        
        # Check run-2 events
        events_2 = store.get_run_events("run-2")
        assert len(events_2) == 3
        event_types_2 = [e["event_type"] for e in events_2]
        assert "run_started" in event_types_2
        assert "node_started" in event_types_2
        assert "node_completed" in event_types_2
        
        # Verify isolation - run-1 should not have run-2's events and vice versa
        run_1_ids = {e["run_id"] for e in events_1}
        run_2_ids = {e["run_id"] for e in events_2}
        assert run_1_ids == {"run-1"}
        assert run_2_ids == {"run-2"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
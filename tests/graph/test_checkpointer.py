"""Unit tests for GraphCheckpointer."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from voice_rag_agents.graph.checkpointer import GraphCheckpointer, get_checkpointer
from voice_rag_agents.graph.states import VoiceRAGState


@pytest.mark.graph
class TestGraphCheckpointer:
    """Test GraphCheckpointer functionality."""

    def setup_method(self):
        """Set up temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoint_dir = os.path.join(self.test_dir, "checkpoints")

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_checkpointer_initialization(self):
        """Test checkpointer initialization."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        assert cp.checkpoint_dir == self.checkpoint_dir
        assert os.path.exists(self.checkpoint_dir)

    def test_get_checkpointer_default(self):
        """Test get_checkpointer with default directory."""
        cp = get_checkpointer()
        assert isinstance(cp, GraphCheckpointer)
        # Default directory should exist or be creatable

    def test_get_checkpointer_custom_dir(self):
        """Test get_checkpointer with custom directory."""
        custom_dir = os.path.join(self.test_dir, "custom")
        cp = get_checkpointer(custom_dir)
        assert cp.checkpoint_dir == custom_dir
        assert os.path.exists(custom_dir)

    def test_save_and_load_state(self):
        """Test saving and loading state."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        
        test_state: VoiceRAGState = {
            "run_id": "test-run-123",
            "request_type": "query",
            "user_id": "test-user",
            "session_id": "test-session",
            "created_at": "2024-01-01T00:00:00Z",
            "runtime_profile": "mock",
            "input_text": "What is the answer?",
            "answer": "This is a test answer.",
            "errors": [{"code": "TEST", "message": "test error"}],
            "warnings": ["test warning"]
        }
        
        # Save state
        cp.save("test-run-123", test_state)
        
        # Verify file exists
        checkpoint_file = os.path.join(self.checkpoint_dir, "test-run-123.json")
        assert os.path.exists(checkpoint_file)
        
        # Load state
        loaded_state = cp.load("test-run-123")
        assert loaded_state is not None
        assert loaded_state["run_id"] == "test-run-123"
        assert loaded_state["request_type"] == "query"
        assert loaded_state["input_text"] == "What is the answer?"
        assert loaded_state["answer"] == "This is a test answer."
        assert len(loaded_state.get("errors", [])) == 1
        assert loaded_state["errors"][0]["code"] == "TEST"
        assert loaded_state["warnings"] == ["test warning"]

    def test_load_nonexistent_checkpoint(self):
        """Test loading a nonexistent checkpoint."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        result = cp.load("nonexistent-run")
        assert result is None

    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        
        test_state: VoiceRAGState = {
            "run_id": "test-run-to-delete",
            "request_type": "query",
            "input_text": "test"
        }
        
        # Save and verify exists
        cp.save("test-run-to-delete", test_state)
        checkpoint_file = os.path.join(self.checkpoint_dir, "test-run-to-delete.json")
        assert os.path.exists(checkpoint_file)
        
        # Delete and verify removed
        result = cp.delete("test-run-to-delete")
        assert result is True
        assert not os.path.exists(checkpoint_file)
        
        # Try to delete again (should return False)
        result = cp.delete("test-run-to-delete")
        assert result is False

    def test_delete_nonexistent_checkpoint(self):
        """Test deleting a nonexistent checkpoint."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        result = cp.delete("nonexistent-run")
        assert result is False

    def test_list_checkpoints(self):
        """Test listing checkpoints."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        
        # Initially empty
        assert cp.list_checkpoints() == []
        
        # Add some checkpoints
        states = [
            {"run_id": "run-1", "request_type": "query", "input_text": "test1"},
            {"run_id": "run-2", "request_type": "ingest", "input_documents": []},
            {"run_id": "run-3", "request_type": "admin", "command": "health"}
        ]
        
        for state in states:
            cp.save(state["run_id"], state)
        
        # List should contain all three
        checkpoints = sorted(cp.list_checkpoints())
        expected = sorted(["run-1", "run-2", "run-3"])
        assert checkpoints == expected
        
        # Delete one and verify
        cp.delete("run-2")
        remaining = sorted(cp.list_checkpoints())
        expected = sorted(["run-1", "run-3"])
        assert remaining == expected

    def test_save_state_without_run_id(self):
        """Test saving state without run_id raises error."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        
        test_state: VoiceRAGState = {
            "request_type": "query",
            "input_text": "test"
            # No run_id
        }
        
        with pytest.raises(ValueError, match="run_id is required"):
            cp.save("", test_state)  # Empty run_id
        
        with pytest.raises(ValueError, match="run_id is required"):
            cp.save(None, test_state)  # None run_id

    def test_state_with_non_serializable_objects(self):
        """Test saving state with non-serializable objects."""
        cp = GraphCheckpointer(self.checkpoint_dir)
        
        # State with a non-serializable object (lambda function)
        test_state: VoiceRAGState = {
            "run_id": "test-non-serializable",
            "request_type": "query",
            "input_text": "test",
            "non_serializable": lambda x: x  # This won't JSON serialize
        }
        
        # Should not raise - converts to string
        cp.save("test-non-serializable", test_state)
        
        # Load and verify it's stored as string
        loaded = cp.load("test-non-serializable")
        assert loaded is not None
        assert isinstance(loaded["non_serializable"], str)
        assert "<lambda>" in loaded["non_serializable"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
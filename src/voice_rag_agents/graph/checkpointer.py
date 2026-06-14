"""Simple checkpointer for LangGraph state persistence.

Provides basic checkpointing functionality for saving and loading state
to JSON files keyed by run_id for resumable ingestion.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from voice_rag_agents.graph.states import VoiceRAGState


class GraphCheckpointer:
    """Simple checkpoint interface that saves/loads state dicts to JSON files.
    
    Does NOT need to be a full LangGraph BaseCheckpointSaver unless you want
    to implement that interface. For the skeleton, we provide basic save/load
    functionality keyed by run_id.
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        """Initialize the checkpointer.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _get_checkpoint_path(self, run_id: str) -> str:
        """Get the file path for a run_id checkpoint."""
        return os.path.join(self.checkpoint_dir, f"{run_id}.json")

    def save(self, run_id: str, state: VoiceRAGState) -> None:
        """Save state to a JSON file keyed by run_id.
        
        Args:
            run_id: Unique identifier for the run
            state: VoiceRAGState to save
        """
        if not run_id:
            raise ValueError("run_id is required for checkpointing")
        
        checkpoint_path = self._get_checkpoint_path(run_id)
        
        # Convert state to dict for JSON serialization
        # Handle any non-serializable objects by converting to string
        state_dict = {}
        for key, value in state.items():
            try:
                json.dumps(value)  # Test if serializable
                state_dict[key] = value
            except (TypeError, ValueError):
                # If not serializable, convert to string
                state_dict[key] = str(value)
        
        with open(checkpoint_path, 'w') as f:
            json.dump(state_dict, f, indent=2, default=str)

    def load(self, run_id: str) -> Optional[VoiceRAGState]:
        """Load state from a JSON file keyed by run_id.
        
        Args:
            run_id: Unique identifier for the run
            
        Returns:
            VoiceRAGState if found, None otherwise
        """
        if not run_id:
            return None
            
        checkpoint_path = self._get_checkpoint_path(run_id)
        
        if not os.path.exists(checkpoint_path):
            return None
        
        try:
            with open(checkpoint_path, 'r') as f:
                state_dict = json.load(f)
            return state_dict  # type: ignore[return-value]
        except (json.JSONDecodeError, IOError):
            return None

    def delete(self, run_id: str) -> bool:
        """Delete checkpoint for a run_id.
        
        Args:
            run_id: Unique identifier for the run
            
        Returns:
            True if deleted, False if not found
        """
        if not run_id:
            return False
            
        checkpoint_path = self._get_checkpoint_path(run_id)
        
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            return True
        return False

    def list_checkpoints(self) -> list[str]:
        """List all available checkpoint run_ids.
        
        Returns:
            List of run_ids for which checkpoints exist
        """
        if not os.path.exists(self.checkpoint_dir):
            return []
        
        checkpoint_files = [f for f in os.listdir(self.checkpoint_dir) 
                          if f.endswith('.json')]
        return [f[:-5] for f in checkpoint_files]  # Remove .json extension


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def get_checkpointer(checkpoint_dir: str = "./checkpoints") -> GraphCheckpointer:
    """Get a GraphCheckpointer instance.
    
    Args:
        checkpoint_dir: Directory to store checkpoint files
        
    Returns:
        GraphCheckpointer instance
    """
    return GraphCheckpointer(checkpoint_dir)


if __name__ == "__main__":
    # Simple test
    checkpointer = get_checkpointer("./test_checkpoints")
    
    test_state: VoiceRAGState = {
        "run_id": "test-run-123",
        "request_type": "query",
        "user_id": "test-user",
        "input_text": "What is the answer?",
        "answer": "This is a test answer."
    }
    
    # Test save
    checkpointer.save("test-run-123", test_state)
    print("Checkpoint saved")
    
    # Test load
    loaded_state = checkpointer.load("test-run-123")
    print(f"Loaded state: {loaded_state}")
    
    # Test list
    checkpoints = checkpointer.list_checkpoints()
    print(f"Available checkpoints: {checkpoints}")
    
    # Test delete
    deleted = checkpointer.delete("test-run-123")
    print(f"Deleted checkpoint: {deleted}")
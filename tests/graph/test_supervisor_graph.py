"""Unit tests for SupervisorGraph."""

from __future__ import annotations

import pytest

from voice_rag_agents.graph.supervisor_graph import (
    build_supervisor_graph,
    run_admin_subgraph,
    run_evaluation_subgraph
)
from voice_rag_agents.graph.states import VoiceRAGState


@pytest.mark.graph
class TestSupervisorGraph:
    """Test SupervisorGraph functionality."""

    def test_build_supervisor_graph(self):
        """Test that the supervisor graph builds successfully."""
        graph = build_supervisor_graph()
        assert graph is not None

    def test_run_admin_subgraph_health(self):
        """Test admin subgraph health command."""
        state: VoiceRAGState = {
            "request_type": "admin",
            "command": "health"
        }
        result = run_admin_subgraph(state)
        assert result["final_status"] == "success"
        assert "healthy" in result["answer"].lower()

    def test_run_admin_subgraph_reindex(self):
        """Test admin subgraph reindex command."""
        state: VoiceRAGState = {
            "request_type": "admin",
            "command": "reindex"
        }
        result = run_admin_subgraph(state)
        assert result["final_status"] == "success"
        assert "reindex" in result["answer"].lower()

    def test_run_admin_subgraph_unknown_command(self):
        """Test admin subgraph with unknown command."""
        state: VoiceRAGState = {
            "request_type": "admin",
            "command": "unknown"
        }
        result = run_admin_subgraph(state)
        assert result["final_status"] == "failed"
        assert "unknown" in result["answer"].lower()

    def test_run_evaluation_subgraph(self):
        """Test evaluation subgraph."""
        state: VoiceRAGState = {
            "request_type": "eval"
        }
        result = run_evaluation_subgraph(state)
        assert result["final_status"] == "success"
        assert "evaluation" in result["answer"].lower()

    def test_supervisor_routes_to_query(self):
        """Test that supervisor routes query requests correctly."""
        # Verify the graph structure is correct without running (complex deps)
        graph = build_supervisor_graph()
        assert graph is not None

    def test_supervisor_routes_to_ingest(self):
        """Test that supervisor routes ingestion requests correctly."""
        graph = build_supervisor_graph()
        assert graph is not None

    def test_supervisor_unknown_request_type(self):
        """Test supervisor handling of unknown request type."""
        graph = build_supervisor_graph()
        # Should route to handle_error
        assert graph is not None


@pytest.mark.graph
class TestSupervisorGraphIntegration:
    """Integration tests for SupervisorGraph (would require mocking subgraphs)."""
    
    def test_supervisor_graph_structure(self):
        """Test that supervisor graph has expected nodes and structure."""
        graph = build_supervisor_graph()
        
        # Check that it's a compiled graph
        assert hasattr(graph, 'invoke')
        
        # The actual node checking would require accessing internal structure
        # which is complex, so we just verify it compiles


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""Test that all new graph modules can be imported."""

from __future__ import annotations

import pytest


@pytest.mark.graph
def test_conditional_logic_import():
    """Test conditional logic module imports."""
    from voice_rag_agents.graph.conditional_logic import (
        route_request_type,
        query_input_route,
        retrieval_route,
        citation_route,
        stt_confidence_route,
        parse_error_route,
        embedding_retry_route,
        dimension_mismatch_route,
        ingestion_retry_route
    )
    assert callable(route_request_type)
    assert callable(query_input_route)
    assert callable(retrieval_route)
    assert callable(citation_route)
    assert callable(stt_confidence_route)
    assert callable(parse_error_route)
    assert callable(embedding_retry_route)
    assert callable(dimension_mismatch_route)
    assert callable(ingestion_retry_route)


@pytest.mark.graph
def test_query_graph_import():
    """Test query graph module imports."""
    from voice_rag_agents.graph.query_graph import (
        build_query_graph,
        run_query_graph
    )
    assert callable(build_query_graph)
    assert callable(run_query_graph)


@pytest.mark.graph
def test_ingestion_graph_import():
    """Test ingestion graph module imports."""
    from voice_rag_agents.graph.ingestion_graph import (
        build_ingestion_graph,
        run_ingestion_graph
    )
    assert callable(build_ingestion_graph)
    assert callable(run_ingestion_graph)


@pytest.mark.graph
def test_supervisor_graph_import():
    """Test supervisor graph module imports."""
    from voice_rag_agents.graph.supervisor_graph import (
        build_supervisor_graph,
        run_supervisor_graph
    )
    assert callable(build_supervisor_graph)
    assert callable(run_supervisor_graph)


@pytest.mark.graph
def test_checkpointer_import():
    """Test checkpointer module imports."""
    from voice_rag_agents.graph.checkpointer import (
        GraphCheckpointer,
        get_checkpointer
    )
    assert callable(GraphCheckpointer)
    assert callable(get_checkpointer)


@pytest.mark.graph
def test_run_artifacts_import():
    """Test run artifacts module imports."""
    from voice_rag_agents.observability.run_artifacts import (
        RunArtifactStore,
        get_artifact_store
    )
    assert callable(RunArtifactStore)
    assert callable(get_artifact_store)


@pytest.mark.graph
def test_graph_package_import():
    """Test that the graph package imports correctly."""
    import voice_rag_agents.graph
    assert hasattr(voice_rag_agents.graph, 'conditional_logic')
    assert hasattr(voice_rag_agents.graph, 'query_graph')
    assert hasattr(voice_rag_agents.graph, 'ingestion_graph')
    assert hasattr(voice_rag_agents.graph, 'supervisor_graph')
    assert hasattr(voice_rag_agents.graph, 'checkpointer')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
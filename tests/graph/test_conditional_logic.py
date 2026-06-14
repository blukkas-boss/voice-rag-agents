"""Unit tests for conditional logic routing functions."""

from __future__ import annotations

import pytest

from voice_rag_agents.graph.conditional_logic import (
    citation_route,
    dimension_mismatch_route,
    embedding_retry_route,
    ingestion_retry_route,
    parse_error_route,
    query_input_route,
    retrieval_route,
    route_request_type,
    stt_confidence_route,
)


@pytest.mark.graph
class TestConditionalLogic:
    """Test all conditional routing functions."""

    # -----------------------------------------------------------------------
    # Supervisor routing tests
    # -----------------------------------------------------------------------
    
    def test_route_request_type_ingest(self):
        state = {"request_type": "ingest"}
        assert route_request_type(state) == "ingestion_subgraph"

    def test_route_request_type_query(self):
        state = {"request_type": "query"}
        assert route_request_type(state) == "query_subgraph"

    def test_route_request_type_admin(self):
        state = {"request_type": "admin"}
        assert route_request_type(state) == "admin_subgraph"

    def test_route_request_type_eval(self):
        state = {"request_type": "eval"}
        assert route_request_type(state) == "evaluation_subgraph"

    def test_route_request_type_error(self):
        state = {"request_type": "invalid"}
        assert route_request_type(state) == "handle_error"

    def test_route_request_type_none(self):
        state = {"request_type": None}
        assert route_request_type(state) == "handle_error"

    def test_route_request_type_missing(self):
        state = {}
        assert route_request_type(state) == "handle_error"

    # -----------------------------------------------------------------------
    # QueryGraph routing tests
    # -----------------------------------------------------------------------
    
    def test_query_input_route_voice(self):
        state = {"input_audio_path": "/tmp/test.wav"}
        assert query_input_route(state) == "voice"

    def test_query_input_route_text(self):
        state = {"input_text": "What is the answer?"}
        assert query_input_route(state) == "text"

    def test_query_input_route_error(self):
        state = {}
        assert query_input_route(state) == "error"

    def test_query_input_route_both_prefers_voice(self):
        state = {
            "input_audio_path": "/tmp/test.wav",
            "input_text": "What is the answer?"
        }
        assert query_input_route(state) == "voice"

    def test_retrieval_route_has_results(self):
        state = {"retrieval_results": [{"id": "1"}]}
        assert retrieval_route(state) == "has_results"

    def test_retrieval_route_no_results(self):
        state = {"retrieval_results": []}
        assert retrieval_route(state) == "no_results"

    def test_retrieval_route_error(self):
        state = {
            "errors": [{"code": "TEST_ERROR", "message": "test"}],
            "retrieval_results": [{"id": "1"}]
        }
        assert retrieval_route(state) == "error"

    def test_citation_route_valid(self):
        state = {
            "answer": "The answer is [S1]",
            "citations": [{"label": "S1", "chunk_id": "c1"}]
        }
        assert citation_route(state) == "valid"

    def test_citation_route_retry_first_attempt(self):
        state = {
            "answer": "The answer",  # No citations
            "citations": [],
            "retries": {"citation_validation": 0}
        }
        assert citation_route(state) == "retry"

    def test_citation_route_invalid_after_retry(self):
        state = {
            "answer": "The answer",  # No citations
            "citations": [],
            "retries": {"citation_validation": 1}
        }
        assert citation_route(state) == "invalid"

    def test_citation_route_no_retries_left(self):
        state = {
            "answer": "The answer",  # No citations
            "citations": [],
            "retries": {"citation_validation": 2}
        }
        assert citation_route(state) == "invalid"

    def test_stt_confidence_route_acceptable(self):
        state = {"stt_confidence": 0.8}
        # Mock the settings to return 0.5 threshold
        import voice_rag_agents.graph.conditional_logic as cl
        original_get_settings = cl.get_settings
        
        class MockSettings:
            stt_confidence_threshold = 0.5
        
        cl.get_settings = lambda: MockSettings()
        try:
            assert stt_confidence_route(state) == "acceptable"
        finally:
            cl.get_settings = original_get_settings

    def test_stt_confidence_route_low(self):
        state = {"stt_confidence": 0.3}
        # Mock the settings to return 0.5 threshold
        import voice_rag_agents.graph.conditional_logic as cl
        original_get_settings = cl.get_settings
        
        class MockSettings:
            stt_confidence_threshold = 0.5
        
        cl.get_settings = lambda: MockSettings()
        try:
            assert stt_confidence_route(state) == "low"
        finally:
            cl.get_settings = original_get_settings

    def test_stt_confidence_route_none_is_low(self):
        state = {}
        import voice_rag_agents.graph.conditional_logic as cl
        original_get_settings = cl.get_settings
        
        class MockSettings:
            stt_confidence_threshold = 0.5
        
        cl.get_settings = lambda: MockSettings()
        try:
            assert stt_confidence_route(state) == "low"
        finally:
            cl.get_settings = original_get_settings

    # -----------------------------------------------------------------------
    # IngestionGraph routing tests
    # -----------------------------------------------------------------------
    
    def test_parse_error_route_quarantine(self):
        state = {
            "errors": [{"node": "parse_documents", "message": "parse failed"}]
        }
        assert parse_error_route(state) == "quarantine"

    def test_parse_error_route_normalize(self):
        state = {
            "errors": [{"node": "other_node", "message": "other error"}]
        }
        assert parse_error_route(state) == "normalize"

    def test_parse_error_route_no_errors(self):
        state = {}
        assert parse_error_route(state) == "normalize"

    def test_embedding_retry_route_retry(self):
        state = {
            "errors": [{"node": "embed_chunks", "message": "embed failed"}],
            "retries": {"embed_chunks": 0}
        }
        assert embedding_retry_route(state) == "retry"

    def test_embedding_retry_route_validate(self):
        state = {
            "errors": [{"node": "other_node", "message": "other error"}],
            "retries": {"embed_chunks": 0}
        }
        assert embedding_retry_route(state) == "validate"

    def test_embedding_retry_route_error_after_max_retries(self):
        state = {
            "errors": [{"node": "embed_chunks", "message": "embed failed"}],
            "retries": {"embed_chunks": 2}
        }
        assert embedding_retry_route(state) == "error"

    def test_dimension_mismatch_route_error(self):
        state = {
            "errors": [{"code": "EMBEDDING_DIMENSION_MISMATCH", "message": "mismatch"}]
        }
        assert dimension_mismatch_route(state) == "error"

    def test_dimension_mismatch_route_upsert(self):
        state = {
            "errors": [{"code": "OTHER_ERROR", "message": "other error"}]
        }
        assert dimension_mismatch_route(state) == "upsert"

    def test_ingestion_retry_route_retry(self):
        state = {
            "errors": [{"node": "upsert_records", "message": "upsert failed"}],
            "retries": {"upsert_records": 0}
        }
        assert ingestion_retry_route(state) == "retry"

    def test_ingestion_retry_route_verify(self):
        state = {
            "errors": [{"node": "other_node", "message": "other error"}],
            "retries": {"upsert_records": 0}
        }
        assert ingestion_retry_route(state) == "verify"

    def test_ingestion_retry_route_error_after_max_retries(self):
        state = {
            "errors": [{"node": "upsert_records", "message": "upsert failed"}],
            "retries": {"upsert_records": 2}
        }
        assert ingestion_retry_route(state) == "error"
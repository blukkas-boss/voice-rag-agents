"""Provider interfaces for agents (retriever, reranker, prompt builder, …).

These are the *freeze-point* contracts that graph nodes depend on.
See ``docs/blueprint/09_MODULE_CONTRACTS_AND_INTERFACES.md`` for the
authoritative specification.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from voice_rag_agents.graph.states import SearchResult
from voice_rag_agents.model_clients.interfaces import ChatMessage


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


class Retriever(Protocol):
    """Retrieval provider interface.

    May embed the query internally or receive vectors from graph state
    depending on the LangGraph node wiring.
    """

    def retrieve(
        self,
        query: str,
        filters: dict | None = None,
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Retrieve top-*k* chunks for *query*, optionally filtered."""
        ...


# ---------------------------------------------------------------------------
# Reranker
# ---------------------------------------------------------------------------


class Reranker(Protocol):
    """Reranker interface for post-retrieval reranking."""

    def rerank(
        self, query: str, results: list[SearchResult]
    ) -> list[SearchResult]:
        """Rereturn a reranked list of search results."""
        ...


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


class PromptBuildRequest(BaseModel):
    question: str
    context_chunks: list[SearchResult]
    conversation_summary: str | None = None
    instructions: dict = Field(default_factory=dict)


class PromptBuildResult(BaseModel):
    messages: list[ChatMessage]
    citation_map: dict[str, str]  # label -> chunk_id


class PromptBuilder(Protocol):
    """Build a grounded prompt from a question and retrieved context."""

    def build(self, request: PromptBuildRequest) -> PromptBuildResult:
        ...


# ---------------------------------------------------------------------------
# Citation validator
# ---------------------------------------------------------------------------


class CitationValidationResult(BaseModel):
    valid: bool
    missing_citations: list[str] = Field(default_factory=list)
    unknown_citations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CitationValidator(Protocol):
    """Validate that every citation in an answer maps to a retrieved chunk."""

    def validate(
        self, answer: str, citation_map: dict[str, str]
    ) -> CitationValidationResult:
        ...


# ---------------------------------------------------------------------------
# Evaluation scorer
# ---------------------------------------------------------------------------


class EvaluationScorer(Protocol):
    """Score retrieval/answer quality for the EvaluationGraph."""

    def score_retrieval(
        self, query: str, results: list[SearchResult], expected_chunk_ids: set[str]
    ) -> dict:
        ...

    def score_answer(
        self,
        question: str,
        answer: str,
        citations: list[dict],
        expected_facts: set[str],
    ) -> dict:
        ...

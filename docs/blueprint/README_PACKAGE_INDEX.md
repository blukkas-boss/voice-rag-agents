# Voice RAG Agents - LangGraph Project Blueprint

This Markdown package is a one-shot implementation brief for an agentic AI platform to build a modular, LangGraph-orchestrated, local-first voice-to-answer RAG product.

## One-line work definition

Build a modular, LangGraph-orchestrated, locally deployable voice-to-answer knowledge assistant that captures user voice or text, transcribes speech locally, embeds queries and knowledge assets with NVIDIA Llama Nemotron Embed VL 1B V2, stores vector embeddings and metadata in Milvus, retrieves grounded context, generates cited answers using a locally hosted LLM, and continuously validates the system through an independent automated testing workforce.

## How to use these files

Pass all `.md` files in this folder to the agentic AI platform as project instructions. Start with `00_ONE_SHOT_AGENT_PLATFORM_PROMPT.md`, then give the platform the remaining files as supporting project context.

The expected output from the agentic AI platform is a complete repository, not just documentation. The repository should contain a Python package, LangGraph graphs, integration adapters, deployment scripts, tests, evaluation harness, and operating documentation.

## Files in this package

| File | Purpose |
|---|---|
| `00_ONE_SHOT_AGENT_PLATFORM_PROMPT.md` | Copy/paste master prompt for autonomous execution. |
| `01_WORK_STATEMENT.md` | Defines the work in the three dimensions: work, workforce, and workbench. |
| `02_LANGGRAPH_PRODUCT_ARCHITECTURE.md` | Target architecture, graphs, state, package structure, and product behavior. |
| `03_WORKFORCE_AGENTIC_ROLES.md` | Build workforce: agents, subagents, responsibilities, outputs, and done criteria. |
| `04_SUBAGENT_TASK_BACKLOG.md` | Backlog-ready Kanban tasks for build agents. |
| `05_ORCHESTRATION_PLAN.md` | How the subagent work is assembled into one product. |
| `06_WORKBENCH_REQUIREMENTS.md` | Tools, runtime, environments, repos, local models, vector DB, and secrets. |
| `07_TESTING_WORKFORCE_AND_PLATFORM.md` | Independent testing workforce and automated validation platform. |
| `08_LANGGRAPH_GRAPH_SPEC.md` | Detailed graph, node, edge, state, and conditional routing specification. |
| `09_MODULE_CONTRACTS_AND_INTERFACES.md` | Adapter contracts, API schemas, storage records, environment configuration. |
| `10_AUTONOMOUS_EXECUTION_GUARDRAILS.md` | Execution rules, assumptions, fallback behavior, security and privacy guardrails. |
| `11_TEST_CASE_CATALOG.md` | Detailed test case catalog for ongoing validation. |
| `12_REFERENCES.md` | Public references used to shape the blueprint. |

## Product name used in these instructions

Working repository/package name: `voice_rag_agents`.

The implementation should mirror the modularity pattern used by the referenced TradingAgents project: separate agents, dataflows, graph orchestration, model clients, configuration, and state schemas.

## Core product stack

- LangGraph for orchestration and modular agent workflows.
- Local speech-to-text using Cipher, Whisper.cpp, or a local Whisper-compatible service.
- NVIDIA Llama Nemotron Embed VL 1B V2 as the primary embedding model.
- Milvus as vector database for embeddings and metadata.
- Ollama as the local LLM runtime, with Qwen, Llama, Mistral, or similar local chat models.
- Open WebUI as the user-facing chat/voice UI where practical.
- FastAPI as a local orchestration API for Open WebUI tools, pipelines, or a custom UI.
- Pytest and evaluation suites for automated validation.

## Top-level deliverables expected from the build platform

1. A complete Python package called `voice_rag_agents`.
2. LangGraph graphs for ingestion, query/RAG, administration, and evaluation.
3. Product adapters for STT, embeddings, Milvus, Ollama, Open WebUI, observability, and config.
4. Docker Compose deployment for Milvus, Open WebUI, Ollama, and the orchestration API.
5. A test and evaluation platform with unit, integration, graph-path, RAG quality, STT, performance, security, and regression tests.
6. Clear documentation for install, operation, extension, and troubleshooting.

## Non-negotiable design principles

- Keep the system modular. Every external dependency must sit behind an adapter interface.
- Keep the graph explicit. Agent handoffs, routing, retries, and quality gates must be visible in LangGraph nodes and edges.
- Keep the product local-first. No cloud service should be mandatory for tests or local demo operation.
- Keep retrieval grounded. Answers must cite retrieved chunks or clearly say no evidence was found.
- Keep testing independent. The testing workforce must not simply validate happy paths designed by the build workforce.
- Keep failures recoverable. Long-running ingestion and reindex operations must support checkpointing or resumable progress.

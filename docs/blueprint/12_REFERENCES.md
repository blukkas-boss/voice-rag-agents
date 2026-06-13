# References Used to Shape This Blueprint

These references inform the architecture and product assumptions. Verify versions during implementation because APIs and capabilities can change.

## TradingAgents reference pattern

- TradingAgents repository root: https://github.com/TauricResearch/TradingAgents
- TradingAgents `tradingagents` package: https://github.com/TauricResearch/TradingAgents/tree/main/tradingagents
- TradingAgents package subfolders observed: `agents`, `dataflows`, `graph`, `llm_clients`, `default_config.py`.
- TradingAgents graph folder includes graph setup, conditional logic, checkpointing, propagation, reflection, signal processing, and main graph orchestration.
- TradingAgents README describes a multi-agent framework with analyst, researcher, trader, risk, and portfolio manager teams.

## LangGraph

- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- LangGraph test guide: https://docs.langchain.com/oss/python/langgraph/test
- LangGraph reference: https://reference.langchain.com/python/langgraph
- LangGraph supervisor reference: https://reference.langchain.com/python/langgraph-supervisor

Relevant principles:

- Graph-based orchestration.
- Stateful workflows.
- Persistence/checkpointing.
- Human-in-the-loop.
- Streaming.
- Explicit nodes and conditional edges.
- Testing graph behavior.

## Open WebUI

- Open WebUI getting started: https://docs.openwebui.com/getting-started/
- Open WebUI RAG docs: https://docs.openwebui.com/features/chat-conversations/rag/
- Open WebUI Knowledge docs: https://docs.openwebui.com/features/workspace/knowledge/
- Open WebUI STT docs: https://docs.openwebui.com/category/speech-to-text/
- Open WebUI Ollama connection: https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-ollama/
- Open WebUI provider connection: https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/

Relevant principles:

- Open WebUI can serve as chat UI.
- Open WebUI can connect to Ollama and OpenAI-compatible providers.
- RAG support exists for knowledge bases and retrieved context.
- STT can be configured in multiple ways.

## NVIDIA Nemotron embedding

- NVIDIA Llama Nemotron Embed VL 1B V2 model card: https://build.nvidia.com/nvidia/llama-nemotron-embed-vl-1b-v2/modelcard
- NVIDIA API reference: https://docs.api.nvidia.com/nim/reference/nvidia-llama-nemotron-embed-vl-1b-v2

Relevant principles:

- The model is an embedding model in the NVIDIA NeMo Retriever collection.
- It is designed for information retrieval use cases.
- Implementation should isolate it behind an embedding provider adapter.

## Milvus

- Milvus docs: https://milvus.io/docs
- Build RAG with Milvus: https://milvus.io/docs/build-rag-with-milvus.md
- Build RAG with Milvus and Ollama: https://milvus.io/docs/build_RAG_with_milvus_and_ollama.md

Relevant principles:

- Milvus stores vector embeddings.
- Milvus can support RAG retrieval pipelines.
- Metadata/scalar filtering is important for knowledge-base use cases.

## Ollama

- Ollama as local LLM runtime should be used through an adapter or OpenAI-compatible interface where possible.
- Keep tests independent of real Ollama availability.

## Notes for implementers

- Do not copy TradingAgents code. Mirror the modular pattern and orchestration philosophy.
- Keep official docs as the primary source for provider-specific APIs during implementation.
- Pin dependencies when building the final repository and document upgrade risks.

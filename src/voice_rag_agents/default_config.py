"""Default configuration values for voice_rag_agents.

Every key has a safe default so the system can boot without a ``.env`` file
and without any secrets loaded.  Environment variables prefixed
``VOICE_RAG_`` override these defaults via :mod:`config.settings`.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Runtime profile
# ---------------------------------------------------------------------------
PROFILE: str = "mock"  # mock | local | integration | production-local

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
TOP_K: int = 5
CHUNK_SIZE_TOKENS: int = 500
CHUNK_OVERLAP_TOKENS: int = 75

# ---------------------------------------------------------------------------
# Vector collection
# ---------------------------------------------------------------------------
COLLECTION: str = "voice_rag_chunks"

# ---------------------------------------------------------------------------
# Embedding provider (NVIDIA Llama Nemotron Embed VL 1B V2 via OpenAI-compatible)
# ---------------------------------------------------------------------------
EMBEDDING_BASE_URL: str = ""
EMBEDDING_MODEL: str = "nvidia/llama-nemotron-embed-vl-1b-v2"
EMBEDDING_DIM: int = 2048
EMBEDDING_API_KEY: str = ""

# ---------------------------------------------------------------------------
# LLM provider (Ollama / OpenAI-compatible)
# ---------------------------------------------------------------------------
LLM_BASE_URL: str = "http://localhost:11434/v1"
LLM_MODEL: str = "llama3.1"
LLM_API_KEY: str = ""

# ---------------------------------------------------------------------------
# Milvus
# ---------------------------------------------------------------------------
MILVUS_URI: str = "http://localhost:19530"

# ---------------------------------------------------------------------------
# STT
# ---------------------------------------------------------------------------
STT_PROVIDER: str = "mock"
STT_COMMAND: str = ""
STT_CONFIDENCE_THRESHOLD: float = 0.5

# ---------------------------------------------------------------------------
# Files / safety
# ---------------------------------------------------------------------------
INPUT_DIR: str = "./data/input"
MAX_FILE_MB: int = 25

# ---------------------------------------------------------------------------
# All keys in one dict (handy for Iterate / wire commands)
# ---------------------------------------------------------------------------
DEFAULTS: dict = {
    "VOICE_RAG_PROFILE": str(PROFILE),
    "VOICE_RAG_TOP_K": str(TOP_K),
    "VOICE_RAG_CHUNK_SIZE_TOKENS": str(CHUNK_SIZE_TOKENS),
    "VOICE_RAG_CHUNK_OVERLAP_TOKENS": str(CHUNK_OVERLAP_TOKENS),
    "VOICE_RAG_COLLECTION": str(COLLECTION),
    "VOICE_RAG_EMBEDDING_BASE_URL": str(EMBEDDING_BASE_URL),
    "VOICE_RAG_EMBEDDING_MODEL": str(EMBEDDING_MODEL),
    "VOICE_RAG_EMBEDDING_DIM": str(EMBEDDING_DIM),
    "VOICE_RAG_EMBEDDING_API_KEY": str(EMBEDDING_API_KEY),
    "VOICE_RAG_LLM_BASE_URL": str(LLM_BASE_URL),
    "VOICE_RAG_LLM_MODEL": str(LLM_MODEL),
    "VOICE_RAG_LLM_API_KEY": str(LLM_API_KEY),
    "VOICE_RAG_MILVUS_URI": str(MILVUS_URI),
    "VOICE_RAG_STT_PROVIDER": str(STT_PROVIDER),
    "VOICE_RAG_STT_COMMAND": str(STT_COMMAND),
    "VOICE_RAG_STT_CONFIDENCE_THRESHOLD": str(STT_CONFIDENCE_THRESHOLD),
    "VOICE_RAG_INPUT_DIR": str(INPUT_DIR),
    "VOICE_RAG_MAX_FILE_MB": str(MAX_FILE_MB),
}

#!/usr/bin/env bash
# Healthcheck for voice_rag_agents — prints service + dependency status.
# Safe to run without Docker (reports what's reachable).
set -u

API_URL="${VOICE_RAG_API_URL:-http://localhost:8088}"
MILVUS_URL="${VOICE_RAG_MILVUS_HEALTH:-http://localhost:9091/healthz}"
OLLAMA_URL="${VOICE_RAG_LLM_BASE_URL:-http://localhost:11434}"

check() {
  local name="$1" url="$2"
  if curl -fsS --max-time 5 "$url" >/dev/null 2>&1; then
    echo "  [OK]   $name ($url)"
  else
    echo "  [DOWN] $name ($url)"
  fi
}

echo "voice_rag_agents healthcheck"
echo "API:"
check "api /health" "$API_URL/health"
echo "Dependencies:"
check "milvus" "$MILVUS_URL"
check "ollama" "$OLLAMA_URL/api/tags"
echo "Done."
